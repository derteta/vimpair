from contextlib import contextmanager
from hashlib import sha224
from os import path
import re


FULL_UPDATE_PREFIX = 'VIMPAIR_FULL_UPDATE'
UPDATE_START_PREFIX = 'VIMPAIR_CONTENTS_START'
UPDATE_PART_PREFIX = 'VIMPAIR_CONTENTS_PART'
UPDATE_END_PREFIX = 'VIMPAIR_CONTENTS_END'
CURSOR_POSITION_PREFIX = 'VIMPAIR_CURSOR_POSITION'
TAKE_CONTROL_MESSAGE = 'VIMPAIR_TAKE_CONTROL'
FILE_CHANGE_PREFIX = 'VIMPAIR_FILE_CHANGE'
SAVE_FILE_MESSAGE = 'VIMPAIR_SAVE_FILE'

MESSAGE_LENGTH = 1024
_LENGTH_DIGITS_AND_MARKERS = 3 + 2
_NUM_MARKERS = 2
_UPDATE_START_CONTENTS_LENGTH = \
    MESSAGE_LENGTH - len(UPDATE_START_PREFIX) - _LENGTH_DIGITS_AND_MARKERS
_UPDATE_PART_CONTENTS_LENGTH = \
    MESSAGE_LENGTH - len(UPDATE_PART_PREFIX) - _LENGTH_DIGITS_AND_MARKERS

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
_ensure_callable = lambda call: call if callable(call) else _noop

def generate_contents_update_messages(contents):

    contents_length = len(contents or '')

    def get_number_of_parts(contents):
        length_without_start = contents_length - _UPDATE_START_CONTENTS_LENGTH
        return 1 \
            + length_without_start // _UPDATE_PART_CONTENTS_LENGTH \
            + int(0 < length_without_start % _UPDATE_PART_CONTENTS_LENGTH)

    def get_part_prefix(index, num_parts):
        if num_parts > 1:
            prefixes = num_parts * [UPDATE_PART_PREFIX]
            prefixes[0] = UPDATE_START_PREFIX
            prefixes[-1] = UPDATE_END_PREFIX
            return prefixes[index]
        return FULL_UPDATE_PREFIX

    def get_part_size(contents_size, index, num_parts):
        first_part_size = min(_UPDATE_START_CONTENTS_LENGTH, contents_size)
        if num_parts > 1:
            sizes = num_parts * [_UPDATE_PART_CONTENTS_LENGTH]
            sizes[0] = first_part_size
            sizes[-1] = (contents_size - _UPDATE_START_CONTENTS_LENGTH) \
                    % _UPDATE_PART_CONTENTS_LENGTH
            return sizes[index]
        return first_part_size

    messages = []
    if contents is not None:
        num_parts = get_number_of_parts(contents)
        for index in xrange(0, num_parts):
            prefix = get_part_prefix(index, num_parts)
            part_size = get_part_size(contents_length, index, num_parts)
            part_contents = contents[:part_size]
            messages.append('%s|%d|%s' % (prefix, part_size, part_contents))
            contents = contents[part_size:]
    return messages

def generate_cursor_position_message(line, column):
    line = max(0, line or 0)
    column = max(0, column or 0)
    return '%s|%d|%d' % (CURSOR_POSITION_PREFIX, line, column)

def generate_file_change_message(filename, folderpath=None, conceal_path=False):
    contents = (filename or '').strip()
    if contents and folderpath:
        contents = path.join(
            sha224(folderpath).hexdigest() if conceal_path else folderpath,
            contents
        )
    return '%s|%d|%s' % (FILE_CHANGE_PREFIX, len(contents), contents)

def generate_save_file_message():
    return SAVE_FILE_MESSAGE

def generate_take_control_message():
    return TAKE_CONTROL_MESSAGE


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

    @contextmanager
    def _find_match(self, expression):
        match = re.search(expression, self._current_message, re.DOTALL)
        yield match.groups() if match else None

    @contextmanager
    def _extract_length_and_contents(self, prefix):
        expression = '%s\|(\d+)\|(.*)' % prefix
        with self._find_match(expression) as groups:
            if groups:
                length = int(groups[0])
                contents = groups[1][:length]
                self._remove_from_message('%s|%d|%s' % (prefix, length, contents))
                yield length, contents
            else:
                yield None, None

    def _handle_message_with_length(self, prefix, handler):
        with self._extract_length_and_contents(prefix) as (length, contents):
            if contents != None:
                handler(length, contents)
            return contents != None


    def _contents_update(self):

        def handle(length, contents):
            if length <= len(contents):
                self._pending_update.start(contents)
                self._pending_update.end('')

        return self._handle_message_with_length(FULL_UPDATE_PREFIX, handle)

    def _contents_start(self):
        return self._handle_message_with_length(
            UPDATE_START_PREFIX,
            lambda _, contents: self._pending_update.start(contents)
        )

    def _contents_part(self):
        return self._handle_message_with_length(
            UPDATE_PART_PREFIX,
            lambda length, contents: self._pending_update.add(contents[:length])
        )

    def _contents_end(self):
        return self._handle_message_with_length(
            UPDATE_END_PREFIX,
            lambda _, contents: self._pending_update.end(contents)
        )

    def _file_change(self):

        def handle_file_change(_, contents):
            self._callbacks.file_changed(filename=contents)
            self._pending_update.reset()

        return self._handle_message_with_length(FILE_CHANGE_PREFIX, handle_file_change)

    def _cursor_position(self):
        pattern = '%s\|(\d+)\|(\d+)' % CURSOR_POSITION_PREFIX
        with self._find_match(pattern) as group:
            if group != None:
                line = int(group[0])
                column = int(group[1])
                self._remove_from_message(
                    '%s|%d|%d' % (CURSOR_POSITION_PREFIX, line, column)
                )
                self._callbacks.apply_cursor_position(line, column)
                self._pending_update.reset()
            return group != None

    def _save_file(self):
        with self._find_match(SAVE_FILE_MESSAGE) as groups:
            if groups is not None:
                self._remove_from_message(SAVE_FILE_MESSAGE)
                self._callbacks.save_file()
            return groups is not None

    @contextmanager
    def _current_message_being(self, message):
        self._current_message = self._leftover + message
        yield
        self._leftover = self._current_message.replace(self._leftover, '')
        self._current_message = ''

    @contextmanager
    def _taking_control_when_told(self):
        do_take_control = TAKE_CONTROL_MESSAGE in self._current_message
        self._current_message = self._current_message.split(TAKE_CONTROL_MESSAGE)[0]
        yield
        if do_take_control:
            self._callbacks.take_control()
            self._pending_update.reset()

    def process(self, messages):
        for message in [messages] if isinstance(messages, basestring) else messages:
            with self._current_message_being(message):
                with self._taking_control_when_told():
                    self._process_current_message()

    def _process_current_message(self):
        match = _ANY_PREFIX.search(self._current_message)
        while match is not None:
            process_call = self._prefix_to_process_call[match.group()]
            if not process_call():
                # If there is an error in the matched message
                # (e.g., negative cursor position), process_call will
                # return False. So we discard the message here.
                self._current_message = \
                    self._current_message[match.start() + len(match.group()):]
            match = _ANY_PREFIX.search(self._current_message)
