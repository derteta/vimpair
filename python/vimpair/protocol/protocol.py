from contextlib import contextmanager
import re

from .constants import (
    FULL_UPDATE_PREFIX,
    UPDATE_START_PREFIX,
    UPDATE_PART_PREFIX,
    UPDATE_END_PREFIX,
    CURSOR_POSITION_PREFIX,
    TAKE_CONTROL_MESSAGE,
    FILE_CHANGE_PREFIX,
    SAVE_FILE_MESSAGE,
    MESSAGE_LENGTH,
)


_ANY_PREFIX = re.compile('%s|%s|%s|%s|%s|%s|%s' % (
    FULL_UPDATE_PREFIX,
    CURSOR_POSITION_PREFIX,
    UPDATE_START_PREFIX,
    UPDATE_PART_PREFIX,
    UPDATE_END_PREFIX,
    FILE_CHANGE_PREFIX,
    SAVE_FILE_MESSAGE,
))

_noop = lambda *a, **k: None


class NullCallbacks(object):

    def __init__(self):
        self.update_contents = _noop
        self.apply_cursor_position = _noop
        self.take_control = _noop
        self.file_changed = _noop
        self.save_file = _noop


class PendingUpdate(object):

    def __init__(self, update_callback=None):
        self._contents = None
        self._update_callback = update_callback or _noop

    def start(self, contents):
        self._contents = contents

    def add(self, contents):
        if self._contents is not None:
            self._contents += contents

    def end(self, contents):
        if self._contents is not None:
            self._contents += contents
            self._update_callback(self._contents)
        self.reset()

    def reset(self):
        self._contents = None


class MessageHandler(object):

    class MessageMatchingError(RuntimeError):
        pass

    @staticmethod
    def _find_match(message, expression):
        match = re.search(expression, message, re.DOTALL)
        if not match:
            raise MessageHandler.MessageMatchingError
        return match.groups()

    def __init__(self, callbacks=None):
        self._leftover = ''
        self._current_message = ''
        self._callbacks = callbacks or NullCallbacks()
        self._pending_update = PendingUpdate(
            update_callback=self._callbacks.update_contents
        )
        self._prefix_to_process_call = {
            FULL_UPDATE_PREFIX: self._contents_update,
            CURSOR_POSITION_PREFIX: self._cursor_position,
            UPDATE_START_PREFIX: self._contents_start,
            UPDATE_PART_PREFIX: self._contents_part,
            UPDATE_END_PREFIX: self._contents_end,
            FILE_CHANGE_PREFIX: self._file_change,
            SAVE_FILE_MESSAGE: self._save_file,
        }

    def _remove_from_message(self, string):
        self._current_message = self._current_message.replace(string, '')

    def _extract_length_and_contents(self, prefix):
        groups = self._find_match(self._current_message, '%s\|(\d+)\|(.*)' % prefix)
        length = int(groups[0])
        contents = groups[1][:length]
        self._remove_from_message('%s|%d|%s' % (prefix, length, contents))
        return length, contents

    def _handle_message_with_length(self, prefix, handler):
        length, contents =  self._extract_length_and_contents(prefix)
        handler(length, contents)

    def _contents_update(self):

        def handle(length, contents):
            if length <= len(contents):
                self._pending_update.start(contents)
                self._pending_update.end('')

        self._handle_message_with_length(FULL_UPDATE_PREFIX, handle)

    def _contents_start(self):
        self._handle_message_with_length(
            UPDATE_START_PREFIX,
            lambda _, contents: self._pending_update.start(contents)
        )

    def _contents_part(self):
        self._handle_message_with_length(
            UPDATE_PART_PREFIX,
            lambda length, contents: self._pending_update.add(contents[:length])
        )

    def _contents_end(self):
        self._handle_message_with_length(
            UPDATE_END_PREFIX,
            lambda _, contents: self._pending_update.end(contents)
        )

    def _file_change(self):

        def handle_file_change(_, contents):
            self._callbacks.file_changed(filename=contents)
            self._pending_update.reset()

        self._handle_message_with_length(FILE_CHANGE_PREFIX, handle_file_change)

    def _cursor_position(self):
        pattern = '%s\|(\d+)\|(\d+)' % CURSOR_POSITION_PREFIX
        groups = self._find_match(self._current_message, pattern)
        line, column = map(int, groups[:2])
        self._remove_from_message('%s|%d|%d' % (CURSOR_POSITION_PREFIX, line, column))
        self._callbacks.apply_cursor_position(line, column)
        self._pending_update.reset()

    def _save_file(self):
        groups = self._find_match(self._current_message, SAVE_FILE_MESSAGE)
        self._remove_from_message(SAVE_FILE_MESSAGE)
        self._callbacks.save_file()

    @contextmanager
    def _taking_control_when_told(self):
        do_take_control = TAKE_CONTROL_MESSAGE in self._current_message
        self._current_message = self._current_message.split(TAKE_CONTROL_MESSAGE)[0]
        yield
        if do_take_control:
            self._callbacks.take_control()
            self._pending_update.reset()
            self._leftover = ''

    def process(self, messages):
        all_messages = reduce(lambda s1, s2: s1 + s2, messages or [''])
        self._current_message = self._leftover + all_messages
        with self._taking_control_when_told():
            self._process_current_message()
            self._leftover = self._current_message.replace(self._leftover, '')

    def _process_current_message(self):
        match = _ANY_PREFIX.search(self._current_message)
        while match is not None:
            try:
                process_call = self._prefix_to_process_call[match.group()]
                process_call()
            except MessageHandler.MessageMatchingError:
                # This can happen if the contained message doesn't have
                # the correct form (i.e., negative cursor position).
                # So we discard the message here.
                self._current_message = \
                    self._current_message[match.start() + len(match.group()):]
            match = _ANY_PREFIX.search(self._current_message)
