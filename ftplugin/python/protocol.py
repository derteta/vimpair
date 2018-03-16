FULL_UPDATE_PREFIX = 'VIMPAIR_FULL_UPDATE'


def generate_contents_update_message(contents):
    return '%s|%d|%s' % (FULL_UPDATE_PREFIX, len(contents), contents) \
        if contents \
        else ''

def generate_cursor_position_message(line, column):
    line = max(0, line or 0)
    column = max(0, column or 0)
    return 'VIMPAIR_CURSOR_POSITION|%d|%d' % (line, column)
