import re


FULL_UPDATE_PREFIX = 'VIMPAIR_FULL_UPDATE'
CURSOR_POSITION_PREFIX = 'VIMPAIR_CURSOR_POSITION'


_noop = lambda *a, **k: None
_ensure_callable = lambda call: call if callable(call) else _noop

def generate_contents_update_messages(contents):
    return ['%s|%d|%s' % (FULL_UPDATE_PREFIX, len(contents), contents)] \
        if contents \
        else []

def generate_cursor_position_message(line, column):
    line = max(0, line or 0)
    column = max(0, column or 0)
    return '%s|%d|%d' % (CURSOR_POSITION_PREFIX, line, column)

def process_message(message, update_contents, apply_cursor_position):

    def _contents_update(groups):
        length = int(groups[0])
        contents = groups[1]
        if length == len(contents):
            _ensure_callable(update_contents)(contents)

    def _cursor_position(groups):
        line = int(groups[0])
        column = int(groups[1])
        _ensure_callable(apply_cursor_position)(line, column)

    if message:
        for regexp, call in (
            ('%s\|(\d+)\|(.*)' % FULL_UPDATE_PREFIX, _contents_update),
            ('%s\|(\d+)\|(\d+)$' % CURSOR_POSITION_PREFIX, _cursor_position),
        ):
            matches = re.match(regexp, message, re.DOTALL)
            if matches:
                call(matches.groups())
                return
