from unittest import TestCase
from mock import Mock
from ddt import data, ddt, unpack

from ..protocol import (
    CURSOR_POSITION_PREFIX,
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


@ddt
class ProcessMessageFullUpdateTests(TestCase):

    def test_calls_update_contents_for_update_message(self):
        update_contents = Mock()
        # not checking for FULL_UPDATE_PREFIX to prevent false positives
        message = 'VIMPAIR_FULL_UPDATE|14|Some Contents.'

        process_message(message, update_contents, None)

        update_contents.assert_called()

    @data(
        ('long_contents',            '|14|', 'Some Contents.'),
        ('short_contents',           '|5|',  'Short'),
        ('contents_with_linebreaks', '|14|', 'Some\nContents.'),
    )
    @unpack
    def test_calls_update_contents(self, _name, length, contents):
        update_contents = Mock()
        message = FULL_UPDATE_PREFIX + length + contents

        process_message(message, update_contents, None)

        update_contents.assert_called_with(contents)

    def test_does_not_call_update_contents_if_it_is_not_callable(self):
        message = FULL_UPDATE_PREFIX + '|5|Short'

        process_message(message, 'update_contents', None)

    @data(
        ('empty_message',      ''),
        ('wrong_length',       FULL_UPDATE_PREFIX + '|123456|Short'),
        ('nonnumeric_length',  FULL_UPDATE_PREFIX + '|five|Short'),
        ('empty_length',       FULL_UPDATE_PREFIX + '||Short'),
        ('empty_contents',     FULL_UPDATE_PREFIX + '|0|'),
        ('missing_1st_marker', FULL_UPDATE_PREFIX + '|Some Contents.'),
        ('missing_2nd_marker', FULL_UPDATE_PREFIX + '|14Some Contents.'),
        ('no_markers',         FULL_UPDATE_PREFIX + 'Contents.'),
        ('incomplete_prefix',  'IMPAIR_FULL_UPDATE|14|Some Contents.'),
        ('incorrect_prefix',   'VIMPAIR_DULL_UPDATE|14|Some Contents.'),
        ('other_valid_prefix', CURSOR_POSITION_PREFIX + '|1|1'),
    )
    @unpack
    def test_does_not_call_update_contents(self, _name, message):
        update_contents = Mock()

        process_message(message, update_contents, None)

        update_contents.assert_not_called()


@ddt
class ProcessMessageCursorPositionTests(TestCase):

    @data(
        ('single_digit_coordinates', CURSOR_POSITION_PREFIX + '|1|1',   (1,1)),
        ('double_digit_coordinates', CURSOR_POSITION_PREFIX + '|22|33', (22,33)),
    )
    @unpack
    def test_calls_apply_cursor_position(self, _name, message, expected_coordinates):
        apply_cursor_position = Mock()

        process_message(message, None, apply_cursor_position)

        apply_cursor_position.assert_called_with(*expected_coordinates)

    def test_does_not_call_apply_cursor_position_if_it_is_not_callable(self):
        # not checking for CURSOR_POSITION_PREFIX to prevent false positives
        message = 'VIMPAIR_CURSOR_POSITION|22|33'

        process_message(message, None, 'apply_cursor_position')

    @data(
        ('empty_message',  ''),
        ('nonnumeric_line',     CURSOR_POSITION_PREFIX + '|one|1'),
        ('nonnumeric_column',   CURSOR_POSITION_PREFIX + '|1|one'),
        ('empty_line',          CURSOR_POSITION_PREFIX + '||1'),
        ('empty_column',        CURSOR_POSITION_PREFIX + '|1|'),
        ('missing_1st_marker',  CURSOR_POSITION_PREFIX + '|1'),
        ('missing_2nd_marker',  CURSOR_POSITION_PREFIX + '|11'),
        ('no_markers',          CURSOR_POSITION_PREFIX + '11'),
        ('incomplete_prefix',   'IMPAIR_CURSOR_POSITION|1|1'),
        ('incorrect_prefix',    'VIMPAIR_TURSOR_POSITION|1|1'),
        ('negative_line',       CURSOR_POSITION_PREFIX + '|-1|1'),
        ('negative_column',     CURSOR_POSITION_PREFIX + '|1|-1'),
        ('float_line_number',   CURSOR_POSITION_PREFIX + '|1.0|1'),
        ('float_column_number', CURSOR_POSITION_PREFIX + '|1|1.0'),
        ('other_valid_prefix',  FULL_UPDATE_PREFIX + '|14|Some Contents.'),
    )
    @unpack
    def test_does_not_call_apply_cursor_position(self, _name, message):
        apply_cursor_position = Mock()

        process_message(message, None, apply_cursor_position)

        apply_cursor_position.assert_not_called()
