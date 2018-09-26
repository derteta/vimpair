from mock import Mock
from unittest import TestCase

from ..vim_interface import (
    apply_contents_update,
    apply_cursor_position,
    get_current_contents,
    get_current_filename,
    get_current_path,
    get_cursor_position,
    switch_to_buffer,
)


def mock_vim_with_contents(contents):
    return Mock(current=Mock(buffer=contents))

def mock_vim_with_cursor(cursor, contents=None):
    vim = Mock(current=Mock(window=Mock(cursor=cursor)))
    vim.current.buffer = contents
    return vim


class GetCurrentContentsTests(TestCase):

    def test_returns_empty_string_without_vim(self):
        vim = None
        self.assertEqual(get_current_contents(vim=vim), '')

    def test_returns_empty_string_without_current(self):
        vim = Mock(current=None)
        self.assertEqual(get_current_contents(vim=vim), '')

    def test_returns_empty_string_without_buffer(self):
        vim = mock_vim_with_contents(None)
        self.assertEqual(get_current_contents(vim=vim), '')

    def test_returns_single_line_as_string(self):
        vim =mock_vim_with_contents(['1'])
        self.assertEqual(get_current_contents(vim=vim), '1')

    def test_returns_multiple_lines_as_string_with_linebreaks(self):
        vim = mock_vim_with_contents(['1', '2', '3'])
        self.assertEqual(get_current_contents(vim=vim), '1\n2\n3')


class GetCursorPositionTests(TestCase):

    def test_returns_zero_zero_without_vim(self):
        vim = None
        self.assertEqual(get_cursor_position(vim=vim), (0, 0))

    def test_returns_zero_zero_without_current(self):
        vim = Mock(current=None)
        self.assertEqual(get_cursor_position(vim=vim), (0, 0))

    def test_returns_zero_zero_without_window(self):
        vim = Mock(current=Mock(window=None))
        self.assertEqual(get_cursor_position(vim=vim), (0, 0))

    def test_returns_zero_zero_without_cursor(self):
        vim = mock_vim_with_cursor(None)
        self.assertEqual(get_cursor_position(vim=vim), (0, 0))

    def test_returns_zero_based_line(self):
        vim = mock_vim_with_cursor((1, 0))
        line, _column = get_cursor_position(vim=vim)
        self.assertEqual(line, 0)

    def test_returns_zero_for_negative_line_values(self):
        vim = mock_vim_with_cursor((-1, 0))
        line, _column = get_cursor_position(vim=vim)
        self.assertEqual(line, 0)

    def test_returns_column_as_reported(self):
        vim = mock_vim_with_cursor((1, 7))
        _line, column = get_cursor_position(vim=vim)
        self.assertEqual(column, 7)

    def test_returns_zero_for_negative_column_values(self):
        vim = mock_vim_with_cursor((1, -7))
        _line, column = get_cursor_position(vim=vim)
        self.assertEqual(column, 0)


class ApplyCurrentContentsTests(TestCase):

    def test_noop_without_vim(self):
        vim = None
        apply_contents_update('This is one line.', vim=vim)

    def test_noop_without_current(self):
        vim = Mock(current=None)
        apply_contents_update('This is one line.', vim=vim)

    def test_noop_without_buffer(self):
        vim = mock_vim_with_contents(None)
        apply_contents_update('This is one line.', vim=vim)

    def test_applies_single_line_string(self):
        vim = mock_vim_with_contents([''])

        apply_contents_update('This is one line.', vim=vim)

        self.assertEqual(vim.current.buffer, ['This is one line.'])

    def test_applies_multiple_line_string(self):
        vim = mock_vim_with_contents([''])

        apply_contents_update(
            'This is one line.\nThis is another line.',
            vim=vim
        )

        self.assertEqual(
            vim.current.buffer,
            ['This is one line.', 'This is another line.']
        )


class ApplyCursorPositionTests(TestCase):

    def test_noop_without_vim(self):
        vim = None
        apply_cursor_position(0, 0, vim=vim)

    def test_noop_without_current(self):
        vim = Mock(current=None)
        apply_cursor_position(0, 0, vim=vim)

    def test_noop_without_window(self):
        vim = Mock(current=Mock(window=None, buffer=['Just one line.']))
        apply_cursor_position(0, 0, vim=vim)

    def test_noop_if_given_line_is_outside_buffer(self):
        vim = mock_vim_with_cursor((1, 0), contents=['Just one line.'])

        apply_cursor_position(1000000, 0, vim=vim)

        self.assertEqual(vim.current.window.cursor, (1, 0))

    def test_noop_if_given_column_is_outside_buffer(self):
        vim = mock_vim_with_cursor((1, 0), contents=['Just one line.'])

        apply_cursor_position(0, 1000000, vim=vim)

        self.assertEqual(vim.current.window.cursor, (1, 0))

    def test_sets_cursor_to_one_based_valid_line(self):
        vim = mock_vim_with_cursor(
            (1, 0),
            contents=['This is line one.', 'This is line two']
        )

        apply_cursor_position(0, 10, vim=vim)

        self.assertEqual(vim.current.window.cursor[0], 1)

    def test_sets_cursor_to_zero_based_valid_column(self):
        vim = mock_vim_with_cursor(
            (1, 0),
            contents=['This is line one.', 'This is line two']
        )

        apply_cursor_position(0, 10, vim=vim)

        self.assertEqual(vim.current.window.cursor[1], 10)


class SwitchToBufferTests(TestCase):

    def test_noop_without_vim(self):
        vim = None
        switch_to_buffer(vim=vim)

    def test_creates_new_buffer_with_vim(self):
        vim = Mock()

        switch_to_buffer(vim=vim)

        vim.command.assert_called_with('silent enew')

    def test_provides_new_buffer_with_given_filename_with_vim(self):
        filename = '.vimrc'
        vim = Mock()

        switch_to_buffer(filename=filename, vim=vim)

        vim.command.assert_called_with('silent e! %s' % filename)


class GetCurrentFilenameTests(TestCase):

    def test_returns_empty_string_without_vim(self):
        vim = None
        self.assertEqual(get_current_filename(vim=vim), '')

    def tests_aquires_filename_with_extension_from_vim(self):
        vim = Mock()

        get_current_filename(vim=vim)

        vim.eval.assert_called_with('expand("%:t")')


class GetCurrentPathTests(TestCase):

    def test_returns_empty_string_without_vim(self):
        vim = None
        self.assertEqual(get_current_path(vim=vim), '')

    def tests_aquires_current_files_directory_path_from_vim(self):
        vim = Mock()

        get_current_path(vim=vim)

        vim.eval.assert_called_with('expand("%:p:h")')
