from mock import Mock
from unittest import TestCase
import sys

mock_vim = Mock(current=None)
sys.modules['vim'] = mock_vim
from ..vim_interface import (
    apply_contents_update,
    apply_cursor_position,
    get_current_contents,
    get_current_filename,
    get_current_path,
    get_cursor_position,
    save_current_file,
    switch_to_buffer,
)


def mock_vim_with_contents(contents):
    return Mock(current=Mock(buffer=contents))

def mock_vim_with_cursor(cursor, contents=None):
    vim = Mock(current=Mock(window=Mock(cursor=cursor)))
    vim.current.buffer = contents
    return vim


class GetCurrentContentsTests(TestCase):

    def test_returns_empty_string_without_current(self):
        self.assertEqual(get_current_contents(), '')

    def test_returns_empty_string_without_buffer(self):
        mock_vim.current = Mock(buffer=None)
        self.assertEqual(get_current_contents(), '')

    def test_returns_single_line_as_string(self):
        mock_vim.current = Mock(buffer=['1'])
        self.assertEqual(get_current_contents(), '1')

    def test_returns_multiple_lines_as_string_with_linebreaks(self):
        mock_vim.current = Mock(buffer=['1', '2', '3'])
        self.assertEqual(get_current_contents(), '1\n2\n3')


class GetCursorPositionTests(TestCase):

    def test_returns_zero_zero_without_current(self):
        self.assertEqual(get_cursor_position(), (0, 0))

    def test_returns_zero_zero_without_window(self):
        mock_vim.current = Mock(window=None)
        self.assertEqual(get_cursor_position(), (0, 0))

    def test_returns_zero_zero_without_cursor(self):
        mock_vim.current = Mock(window=Mock(cursor=None))
        self.assertEqual(get_cursor_position(), (0, 0))

    def test_returns_zero_based_line(self):
        mock_vim.current = Mock(window=Mock(cursor=(1, 0)))
        line, _column = get_cursor_position()
        self.assertEqual(line, 0)

    def test_returns_zero_for_negative_line_values(self):
        mock_vim.current = Mock(window=Mock(cursor=(-1, 0)))
        line, _column = get_cursor_position()
        self.assertEqual(line, 0)

    def test_returns_column_as_reported(self):
        mock_vim.current = Mock(window=Mock(cursor=(1, 7)))
        _line, column = get_cursor_position()
        self.assertEqual(column, 7)

    def test_returns_zero_for_negative_column_values(self):
        mock_vim.current = Mock(window=Mock(cursor=(1, -7)))
        _line, column = get_cursor_position()
        self.assertEqual(column, 0)


class ApplyCurrentContentsTests(TestCase):

    def test_noop_without_current(self):
        apply_contents_update('This is one line.')

    def test_noop_without_buffer(self):
        mock_vim.current = Mock(buffer=None)
        apply_contents_update('This is one line.')

    def test_applies_single_line_string(self):
        mock_vim.current = Mock(buffer=[''])

        apply_contents_update('This is one line.')

        self.assertEqual(mock_vim.current.buffer, ['This is one line.'])

    def test_applies_multiple_line_string(self):
        mock_vim.current = Mock(buffer=[''])

        apply_contents_update('This is one line.\nThis is another line.')

        self.assertEqual(
            mock_vim.current.buffer,
            ['This is one line.', 'This is another line.']
        )

    def test_removes_superfluous_lines(self):
        mock_vim.current = Mock(buffer=['1', '2', '3'])

        apply_contents_update('This is one line.\nThis is another line.')

        self.assertEqual(
            mock_vim.current.buffer,
            ['This is one line.', 'This is another line.']
        )


class ApplyCursorPositionTests(TestCase):

    def test_noop_without_current(self):
        apply_cursor_position(0, 0)

    def test_noop_without_window(self):
        mock_vim.current = Mock(window=None, buffer=['Just one line.'])
        apply_cursor_position(0, 0)

    def test_noop_if_given_line_is_outside_buffer(self):
        mock_vim.current = Mock(window=Mock(cursor=(1, 0)), buffer=['Just one line.'])

        apply_cursor_position(1000000, 0)

        self.assertEqual(mock_vim.current.window.cursor, (1, 0))

    def test_noop_if_given_column_is_outside_buffer(self):
        mock_vim.current = Mock(window=Mock(cursor=(1, 0)), buffer=['Just one line.'])

        apply_cursor_position(0, 1000000)

        self.assertEqual(mock_vim.current.window.cursor, (1, 0))

    def test_sets_cursor_to_one_based_valid_line(self):
        mock_vim.current = Mock(
            window=Mock(cursor=(1, 0)),
            buffer=['This is line one.', 'This is line two']
        )

        apply_cursor_position(0, 10)

        self.assertEqual(mock_vim.current.window.cursor[0], 1)

    def test_sets_cursor_to_zero_based_valid_column(self):
        mock_vim.current = Mock(
            window=Mock(cursor=(1, 0)),
            buffer=['This is line one.', 'This is line two']
        )

        apply_cursor_position(0, 10)

        self.assertEqual(mock_vim.current.window.cursor[1], 10)


class SwitchToBufferTests(TestCase):

    def test_creates_new_buffer_with_vim(self):
        mock_vim.command = Mock()

        switch_to_buffer()

        mock_vim.command.assert_called_with('silent enew')

    def test_provides_new_buffer_with_given_filename_with_vim(self):
        filename = '.vimrc'
        mock_vim.command = Mock()

        switch_to_buffer(filename=filename)

        mock_vim.command.assert_called_with('silent e! %s' % filename)


class GetCurrentFilenameTests(TestCase):

    def tests_aquires_filename_with_extension_from_vim(self):
        mock_vim.eval = Mock()

        get_current_filename()

        mock_vim.eval.assert_called_with('expand("%:t")')


class GetCurrentPathTests(TestCase):

    def tests_aquires_current_files_directory_path_from_vim(self):
        mock_vim.eval = Mock()

        get_current_path()

        mock_vim.eval.assert_called_with('expand("%:p:h")')


class SaveFileTests(TestCase):

    def tests_silently_writes_current_buffer_to_given_path(self):
        mock_vim.command = Mock()

        save_current_file('/path/to/file.py')

        mock_vim.command.assert_called_with('silent write! /path/to/file.py')
