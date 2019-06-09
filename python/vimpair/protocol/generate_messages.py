from hashlib import sha224
from os import path

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


_LENGTH_DIGITS_AND_MARKERS = 3 + 2
_NUM_MARKERS = 2
_UPDATE_START_CONTENTS_LENGTH = \
    MESSAGE_LENGTH - len(UPDATE_START_PREFIX) - _LENGTH_DIGITS_AND_MARKERS
_UPDATE_PART_CONTENTS_LENGTH = \
    MESSAGE_LENGTH - len(UPDATE_PART_PREFIX) - _LENGTH_DIGITS_AND_MARKERS

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
        for index in range(0, num_parts):
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
