from unittest import TestCase

from ..protocol import (
    FULL_UPDATE_PREFIX,
    generate_contents_update_message,
    generate_cursor_position_message,
)


class GenerateContentsUpdateMessageTests(TestCase):

    def test_returns_empty_message_if_contents_is_none(self):
        self.assertEqual(generate_contents_update_message(None), '')

    def test_returns_empty_message_if_contents_is_empty(self):
        self.assertEqual(generate_contents_update_message(''), '')

    def test_contents_update_message_starts_with_expected_prefix(self):
        message = generate_contents_update_message('Some contents')

        # not checking for FULL_UPDATE_PREFIX to prevent false positives
        self.assertTrue(message.startswith('VIMPAIR_FULL_UPDATE'), message)

    def test_contents_update_message_contains_content_length(self):
        length_offset = len(FULL_UPDATE_PREFIX)

        message = generate_contents_update_message('Some contents')

        self.assertTrue(message[length_offset:].startswith('|13|'), message)

    def test_linebreaks_are_counted_as_one_character_in_length(self):
        length_offset = len(FULL_UPDATE_PREFIX)

        message = generate_contents_update_message('Some\ncontents')

        self.assertTrue(message[length_offset:].startswith('|13|'), message)

    def test_contents_update_message_ends_with_contents(self):
        length_offset = len(FULL_UPDATE_PREFIX) + 3

        message = generate_contents_update_message('Some contents')

        self.assertTrue(
            message[length_offset:].startswith('|Some contents'),
            message
        )


class GenerateCursorPositionMessageTests(TestCase):

    def assert_returns_zero_zero_with(self, line, column):
        message = generate_cursor_position_message(line, column)

        self.assertTrue(message.endswith('|0|0'), message)


    def test_message_starts_with_expected_prefix(self):
        message = generate_cursor_position_message(None, 0)

        # not checking for CURSOR_POSITION_PREFIX to prevent false positives
        self.assertTrue(message.startswith('VIMPAIR_CURSOR_POSITION'), message)

    def test_returns_zero_zero_if_line_is_none(self):
        self.assert_returns_zero_zero_with(None, 0)

    def test_returns_zero_zero_if_column_is_none(self):
        self.assert_returns_zero_zero_with(0, None)

    def test_returns_zero_zero_if_line_is_negative(self):
        self.assert_returns_zero_zero_with(-2, 0)

    def test_returns_zero_zero_if_column_is_negative(self):
        self.assert_returns_zero_zero_with(0, -1)

    def test_returned_message_contains_valid_line(self):
        message = generate_cursor_position_message(11, 0)

        self.assertTrue(message.endswith('|11|0'), message)

    def test_returned_message_contains_valid_column(self):
        message = generate_cursor_position_message(0, 111)

        self.assertTrue(message.endswith('|0|111'), message)
