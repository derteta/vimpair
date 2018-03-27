from unittest import TestCase
from mock import Mock

from ..protocol import (
    FULL_UPDATE_PREFIX,
    generate_contents_update_message,
    generate_cursor_position_message,
    process_message,
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


class ProcessMessageFullUpdateTests(TestCase):

    def test_calls_update_contents_for_update_message(self):
        update_contents = Mock()
        message = 'VIMPAIR_FULL_UPDATE|14|Some Contents.'

        process_message(message, update_contents, None)

        update_contents.assert_called()

    def test_calls_update_contents_with_long_message_contents(self):
        update_contents = Mock()
        message = 'VIMPAIR_FULL_UPDATE|14|Some Contents.'

        process_message(message, update_contents, None)

        update_contents.assert_called_with('Some Contents.')

    def test_calls_update_contents_with_short_message_contents(self):
        update_contents = Mock()
        message = 'VIMPAIR_FULL_UPDATE|5|Short'

        process_message(message, update_contents, None)

        update_contents.assert_called_with('Short')

    def test_calls_update_contents_with_contents_including_linebreaks(self):
        update_contents = Mock()
        message = 'VIMPAIR_FULL_UPDATE|14|Some\nContents.'

        process_message(message, update_contents, None)

        update_contents.assert_called_with('Some\nContents.')

    def test_does_not_call_update_contents_for_empty_message(self):
        update_contents = Mock()

        process_message('', update_contents, None)

        update_contents.assert_not_called()

    def test_does_not_call_update_contents_if_it_is_not_callable(self):
        message = 'VIMPAIR_FULL_UPDATE|5|Short'

        process_message(message, 'update_contents', None)

    def test_does_not_call_update_contents_for_message_with_wrong_length(self):
        update_contents = Mock()
        message = 'VIMPAIR_FULL_UPDATE|123456|Short'

        process_message(message, update_contents, None)

        update_contents.assert_not_called()

    def test_does_not_call_update_contents_for_message_with_nonnumeric_length(self):
        update_contents = Mock()
        message = 'VIMPAIR_FULL_UPDATE|five|Short'

        process_message(message, update_contents, None)

        update_contents.assert_not_called()

    def test_does_not_call_update_contents_for_message_with_empty_length(self):
        update_contents = Mock()
        message = 'VIMPAIR_FULL_UPDATE||Short'

        process_message(message, update_contents, None)

        update_contents.assert_not_called()

    def test_does_not_call_update_contents_for_message_with_empty_content(self):
        update_contents = Mock()
        message = 'VIMPAIR_FULL_UPDATE|0|'

        process_message(message, update_contents, None)

        update_contents.assert_not_called()

    def test_does_not_call_update_contents_for_message_with_missing_first_marker(self):
        update_contents = Mock()
        message = 'VIMPAIR_FULL_UPDATE14|Some Contents.'

        process_message(message, update_contents, None)

        update_contents.assert_not_called()

    def test_does_not_call_update_contents_for_message_with_missing_second_marker(self):
        update_contents = Mock()
        message = 'VIMPAIR_FULL_UPDATE|14Some Contents.'

        process_message(message, update_contents, None)

        update_contents.assert_not_called()

    def test_does_not_call_update_contents_for_message_without_markers(self):
        update_contents = Mock()
        message = 'VIMPAIR_FULL_UPDATE14Some Contents.'

        process_message(message, update_contents, None)

        update_contents.assert_not_called()

    def test_does_not_call_update_contents_for_message_with_incomplete_prefix(self):
        update_contents = Mock()
        message = 'IMPAIR_FULL_UPDATE|14|Some Contents.'

        process_message(message, update_contents, None)

        update_contents.assert_not_called()

    def test_does_not_call_update_contents_for_message_with_incorrect_prefix(self):
        update_contents = Mock()
        message = 'VIMPAIR_DULL_UPDATE|14|Some Contents.'

        process_message(message, update_contents, None)

        update_contents.assert_not_called()

    def test_does_not_call_update_contents_for_message_with_another_valid_prefix(self):
        update_contents = Mock()
        message = 'VIMPAIR_CURSOR_POSITION|1|1'

        process_message(message, update_contents, None)

        update_contents.assert_not_called()
