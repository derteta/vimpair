from mock import Mock
from unittest import TestCase

from ..vim_interface import get_current_contents, get_cursor_position


def mock_vim_with_contents(contents):
    return Mock(current=Mock(buffer=contents))

def mock_vim_with_cursor(cursor):
    return Mock(current=Mock(window=Mock(cursor=cursor)))


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
