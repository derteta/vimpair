from functools import reduce
import vim


def get_current_contents():
    ''' returns the contents of current buffer/file as one string '''
    try:
        lines = vim.current.buffer
    except AttributeError:
        lines = ['']

    return reduce(lambda l1, l2: l1 + '\n' + l2, lines or [''])


def get_current_filename():
    ''' returns name and extension of the current file '''
    try:
        return vim.eval('expand("%:t")')
    except AttributeError:
        return ''


def get_current_path():
    ''' returns the current file's full path without its name '''
    try:
        return vim.eval('expand("%:p:h")')
    except AttributeError:
        return ''


def get_cursor_position():
    ''' returns a tuple (line, column) of the cursor position '''
    try:
        cursor = vim.current.window.cursor
        line, column = cursor or (1, 0)
        # Vim counts lines 1-based, but columns are 0-based. Unifying.
        return max(0, line - 1), max(0, column)
    except AttributeError:
        return (0, 0)


def apply_contents_update(contents_string):
    try:
        current_buffer = vim.current.buffer
        if current_buffer is not None:
            lines = contents_string.split('\n')
            for index, line in enumerate(lines):
                if index < len(current_buffer):
                    current_buffer[index] = line
                else:
                    current_buffer.append(line)
            del current_buffer[len(lines):]
    except AttributeError:
        pass


def apply_cursor_position(line, column):
    try:
        current_buffer = vim.current.buffer or []
        if line < len(current_buffer) and column < len(current_buffer[line]):
            # Vim counts lines 1-based, this is called with 0-based values.
            vim.current.window.cursor = (line + 1, column)
    except AttributeError:
        pass


def switch_to_buffer(filename=None):
    try:
        vim.command(
            'silent e' + ('! %s' % filename if filename else 'new')
        )
    except AttributeError:
        pass


def save_current_file(full_path):
    try:
        vim.command('silent write! ' + full_path)
    except AttributeError:
        pass


def show_status_message(message):
    if int(vim.eval('g:VimpairShowStatusMessages')) != 0:
        print('Vimpair:', message)
