import re


FULL_UPDATE_PREFIX = 'VIMPAIR_FULL_UPDATE'


_noop = lambda *a, **k: None
_ensure_callable = lambda call: call if callable(call) else _noop

def generate_contents_update_message(contents):
    return '%s|%d|%s' % (FULL_UPDATE_PREFIX, len(contents), contents) \
        if contents \
        else ''

def generate_cursor_position_message(line, column):
    line = max(0, line or 0)
    column = max(0, column or 0)
    return 'VIMPAIR_CURSOR_POSITION|%d|%d' % (line, column)

def process_message(message, update_contents, _):
    if message:
        matches = re.match(
            '%s\|(\d+)\|(.*)' % FULL_UPDATE_PREFIX,
            message,
            re.DOTALL,
        )
        if matches:
            update_contents = _ensure_callable(update_contents)
            groups = matches.groups()
            length = int(groups[0])
            contents = groups[1]
            if length and length == len(contents):
                update_contents(contents)
