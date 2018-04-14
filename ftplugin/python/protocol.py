import re


FULL_UPDATE_PREFIX = 'VIMPAIR_FULL_UPDATE'
UPDATE_START_PREFIX = 'VIMPAIR_CONTENTS_START'
UPDATE_PART_PREFIX = 'VIMPAIR_CONTENTS_PART'
UPDATE_END_PREFIX = 'VIMPAIR_CONTENTS_END'
CURSOR_POSITION_PREFIX = 'VIMPAIR_CURSOR_POSITION'

MESSAGE_LENGTH = 1024
_LENGTH_DIGITS_AND_MARKERS = 3 + 2
_NUM_MARKERS = 2
_UPDATE_START_CONTENTS_LENGTH = \
    MESSAGE_LENGTH - len(UPDATE_START_PREFIX) - _LENGTH_DIGITS_AND_MARKERS
_UPDATE_PART_CONTENTS_LENGTH = \
    MESSAGE_LENGTH - len(UPDATE_PART_PREFIX) - _LENGTH_DIGITS_AND_MARKERS

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
    if contents:
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

def process_message(
    message,
    update_contents,
    apply_cursor_position,
    pending_update=[None],
):

    def _contents_update(groups):
        length = int(groups[0])
        contents = groups[1]
        if length == len(contents):
            _ensure_callable(update_contents)(contents)
        pending_update[0] = None

    def _contents_start(groups):
        length = int(groups[0])
        contents = groups[1]
        if length == len(contents):
            pending_update[0] = contents

    def _contents_part(groups):
        length = int(groups[0])
        contents = groups[1]
        if pending_update[0] and length == len(contents):
            pending_update[0] += contents

    def _contents_end(groups):
        length = int(groups[0])
        contents = groups[1]
        if pending_update[0] and length == len(contents):
            _ensure_callable(update_contents)(
                pending_update[0] + contents
            )
        pending_update[0] = None

    def _cursor_position(groups):
        line = int(groups[0])
        column = int(groups[1])
        _ensure_callable(apply_cursor_position)(line, column)
        pending_update[0] = None

    if message:
        for regexp, call in (
            ('%s\|(\d+)\|(.*)' % FULL_UPDATE_PREFIX, _contents_update),
            ('%s\|(\d+)\|(.*)' % UPDATE_START_PREFIX, _contents_start),
            ('%s\|(\d+)\|(.*)' % UPDATE_PART_PREFIX, _contents_part),
            ('%s\|(\d+)\|(.*)' % UPDATE_END_PREFIX, _contents_end),
            ('%s\|(\d+)\|(\d+)$' % CURSOR_POSITION_PREFIX, _cursor_position),
        ):
            matches = re.match(regexp, message, re.DOTALL)
            if matches:
                call(matches.groups())
                return
        pending_update[0] = None
