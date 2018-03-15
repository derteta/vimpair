FULL_UPDATE_PREFIX = 'VIMPAIR_FULL_UPDATE'


def generate_contents_update_message(contents):
    return '%s|%d|%s' % (FULL_UPDATE_PREFIX, len(contents), contents) \
        if contents \
        else ''
