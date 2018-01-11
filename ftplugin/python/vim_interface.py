def get_current_contents(vim=None):
    ''' returns the contents of current buffer/file as one string '''
    try:
        lines = vim.current.buffer
    except AttributeError:
        lines = ['']

    return reduce(lambda l1, l2: l1 + '\n' + l2, lines or [''])


def get_cursor_position(vim=None):
    ''' returns a tuple (line, column) of the cursor position '''
    try:
        cursor = vim.current.window.cursor
        line, column = cursor or (1, 0)
        # Vim counts lines 1-based, but columns are 0-based. Unifying.
        return max(0, line - 1), max(0, column)
    except AttributeError:
        return (0, 0)
