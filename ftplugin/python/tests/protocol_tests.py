from unittest import TestCase
from mock import Mock
from ddt import data, ddt

from .util import TestContext as TC
from ..protocol import (
    CURSOR_POSITION_PREFIX,
    FULL_UPDATE_PREFIX,
    generate_contents_update_messages,
    generate_cursor_position_message,
    MessageHandler,
    UPDATE_START_PREFIX,
    UPDATE_PART_PREFIX,
    UPDATE_END_PREFIX,
)


def first(iterable):
    return iterable[0]


@ddt
class GenerateContentsUpdateMessageTests(TestCase):

    def test_returns_no_messages_if_contents_is_none(self):
        self.assertEqual(generate_contents_update_messages(None), [])

    def test_returns_no_messages_if_contents_is_empty(self):
        self.assertEqual(generate_contents_update_messages(''), [])

    def test_contents_update_message_starts_with_expected_prefix(self):
        message = first(generate_contents_update_messages('Some contents'))

        # not checking for FULL_UPDATE_PREFIX to prevent false positives
        self.assertTrue(message.startswith('VIMPAIR_FULL_UPDATE'), message)

    def test_contents_update_message_contains_content_length(self):
        length_offset = len(FULL_UPDATE_PREFIX)

        message = first(generate_contents_update_messages('Some contents'))

        self.assertTrue(message[length_offset:].startswith('|13|'), message)

    def test_linebreaks_are_counted_as_one_character_in_length(self):
        length_offset = len(FULL_UPDATE_PREFIX)

        message = first(generate_contents_update_messages('Some\ncontents'))

        self.assertTrue(message[length_offset:].startswith('|13|'), message)

    def test_contents_update_message_ends_with_contents(self):
        length_offset = len(FULL_UPDATE_PREFIX) + 3

        message = first(generate_contents_update_messages('Some contents'))

        self.assertTrue(
            message[length_offset:].startswith('|Some contents'),
            message
        )

    @data(
        TC('two_parts',       length=1024,  expected_num_parts=2),
        TC('three_parts',     length=2048,  expected_num_parts=3),
        # 40960 is the 1st case with 'num_parts != 1 + len(contents) / 1024'
        TC('fourtytwo_parts', length=40960, expected_num_parts=42),
    )
    def test_splits_long_content_into_several_messages(self, context):
        messages = generate_contents_update_messages('#' * context.length)

        actual_num_parts = len(messages)
        self.assertEqual(
            actual_num_parts,
            context.expected_num_parts,
            actual_num_parts
        )

    @data(
        TC('start', index=0,  expected_prefix='VIMPAIR_CONTENTS_START'),
        TC('part',  index=1,  expected_prefix='VIMPAIR_CONTENTS_PART'),
        TC('end',   index=-1, expected_prefix='VIMPAIR_CONTENTS_END'),
    )
    def test_multiple_messages_start_with_special_prefixes(self, context):
        messages = generate_contents_update_messages('#' * 2048)

        message = messages[context.index]
        self.assertTrue(message.startswith(context.expected_prefix), message)

    @data(
        TC(
            'start',
            index=0,
            length_offset=1 + len(UPDATE_START_PREFIX),
            expected_length='997|'
        ),
        TC(
            'part',
            index=1,
            length_offset=1 + len(UPDATE_PART_PREFIX),
            expected_length='998|'
        ),
        TC(
            'end',
            index=-1,
            length_offset=1 + len(UPDATE_END_PREFIX),
            expected_length='55|'
        ),
    )
    def test_multiple_messages_have_the_correct_length_of_the_contained_part(
        self,
        context
    ):
        messages = generate_contents_update_messages('0123456789' * 205)

        message = messages[context.index][context.length_offset:]
        self.assertTrue(message.startswith(context.expected_length), message)

    @data(
        TC('start', index=0,  expected_length=1024),
        TC('part',  index=1,  expected_length=1024),
        TC('end',   index=-1, expected_length=77),
    )
    def test_multiple_messages_have_the_expected_overall_length(self, context):
        messages = generate_contents_update_messages('#' * 2048)

        message = messages[context.index]
        self.assertEqual(len(message), context.expected_length, message)

    @data(
        TC(
            'start',
            index=0,
            length_offset=5 + len(UPDATE_START_PREFIX),
            expected_start_and_end=('0','6'),
        ),
        TC(
            'part',
            index=1,
            length_offset=5 + len(UPDATE_PART_PREFIX),
            expected_start_and_end=('7','4'),
        ),
        TC(
            'end',
            index=-1,
            length_offset=4 + len(UPDATE_END_PREFIX),
            expected_start_and_end=('5','9'),
        ),
    )
    def test_multiple_messages_have_the_expected_contents(self, context):
        messages = generate_contents_update_messages('0123456789' * 201)

        message = messages[context.index]
        actual_start_and_end = (message[context.length_offset], message[-1])
        self.assertEqual(
            actual_start_and_end,
            context.expected_start_and_end,
            actual_start_and_end
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
class MessageHandlerFullUpdateTests(TestCase):

    def setUp(self):
        self.update_contents = Mock()
        self.handler = MessageHandler(update_contents=self.update_contents)


    def test_calls_update_contents_for_update_message(self):
        # not checking for FULL_UPDATE_PREFIX to prevent false positives
        message = 'VIMPAIR_FULL_UPDATE|14|Some Contents.'

        self.handler.process(message)

        self.update_contents.assert_called()

    @data(
        TC('empty_contents',           length='|0|',  contents=''),
        TC('long_contents',            length='|14|', contents='Some Contents.'),
        TC('short_contents',           length='|5|',  contents='Short'),
        TC('contents_with_linebreaks', length='|14|', contents='Some\nContents.'),
    )
    def test_calls_update_contents(self, context):
        message = FULL_UPDATE_PREFIX + context.length + context.contents

        self.handler.process(message)

        self.update_contents.assert_called_with(context.contents)

    def test_does_not_call_update_contents_if_it_is_not_callable(self):
        message = FULL_UPDATE_PREFIX + '|5|Short'

        handler = MessageHandler(update_contents='update_contents')
        handler.process(message)

    @data(
        TC('empty_message',      message=''),
        TC('wrong_length',       message=FULL_UPDATE_PREFIX + '|123456|Short'),
        TC('nonnumeric_length',  message=FULL_UPDATE_PREFIX + '|five|Short'),
        TC('empty_length',       message=FULL_UPDATE_PREFIX + '||Short'),
        TC('missing_1st_marker', message=FULL_UPDATE_PREFIX + '|Some Contents.'),
        TC('missing_2nd_marker', message=FULL_UPDATE_PREFIX + '|14Some Contents.'),
        TC('no_markers',         message=FULL_UPDATE_PREFIX + 'Contents.'),
        TC('incomplete_prefix',  message='IMPAIR_FULL_UPDATE|14|Some Contents.'),
        TC('incorrect_prefix',   message='VIMPAIR_DULL_UPDATE|14|Some Contents.'),
        TC('other_valid_prefix', message=CURSOR_POSITION_PREFIX + '|1|1'),
    )
    def test_does_not_call_update_contents(self, context):
        self.handler.process(context.message)

        self.update_contents.assert_not_called()


@ddt
class MessageHandlerCursorPositionTests(TestCase):

    def setUp(self):
        self.apply_cursor_position = Mock()
        self.handler = MessageHandler(
            apply_cursor_position=self.apply_cursor_position
        )


    @data(
        TC(
            'single_digit_coordinates',
            message=CURSOR_POSITION_PREFIX + '|1|1',
            expected_coordinates=(1,1)
        ),
        TC(
            'double_digit_coordinates',
            message=CURSOR_POSITION_PREFIX + '|22|33',
            expected_coordinates=(22,33)
        ),
    )
    def test_calls_apply_cursor_position(self, context):
        self.handler.process(context.message)

        self.apply_cursor_position.assert_called_with(
            *context.expected_coordinates
        )

    def test_does_not_call_apply_cursor_position_if_it_is_not_callable(self):
        # not checking for CURSOR_POSITION_PREFIX to prevent false positives
        message = 'VIMPAIR_CURSOR_POSITION|22|33'

        handler = MessageHandler(apply_cursor_position='apply_cursor_position')
        handler.process(message)

    @data(
        TC('empty_message',       message=''),
        TC('nonnumeric_line',     message=CURSOR_POSITION_PREFIX + '|one|1'),
        TC('nonnumeric_column',   message=CURSOR_POSITION_PREFIX + '|1|one'),
        TC('empty_line',          message=CURSOR_POSITION_PREFIX + '||1'),
        TC('empty_column',        message=CURSOR_POSITION_PREFIX + '|1|'),
        TC('missing_1st_marker',  message=CURSOR_POSITION_PREFIX + '|1'),
        TC('missing_2nd_marker',  message=CURSOR_POSITION_PREFIX + '|11'),
        TC('no_markers',          message=CURSOR_POSITION_PREFIX + '11'),
        TC('incomplete_prefix',   message='IMPAIR_CURSOR_POSITION|1|1'),
        TC('incorrect_prefix',    message='VIMPAIR_TURSOR_POSITION|1|1'),
        TC('negative_line',       message=CURSOR_POSITION_PREFIX + '|-1|1'),
        TC('negative_column',     message=CURSOR_POSITION_PREFIX + '|1|-1'),
        TC('float_line_number',   message=CURSOR_POSITION_PREFIX + '|1.0|1'),
        TC('float_column_number', message=CURSOR_POSITION_PREFIX + '|1|1.0'),
        TC('other_valid_prefix',  message=FULL_UPDATE_PREFIX + '|14|Some Contents.'),
    )
    def test_does_not_call_apply_cursor_position(self, context):
        self.handler.process(context.message)

        self.apply_cursor_position.assert_not_called()


@ddt
class MessageHandlerSplitContentsTests(TestCase):

    def setUp(self):
        self.update_contents = Mock()
        self.handler = MessageHandler(update_contents=self.update_contents)


    def test_does_not_call_update_contents_when_receiving_only_contents_start(self):
        self.handler.process(UPDATE_START_PREFIX + '|15|First part of a')

        self.update_contents.assert_not_called()

    def test_does_not_call_update_contents_when_receiving_only_contents_end(self):
        self.handler.process(UPDATE_END_PREFIX + '|16| longer message.')

        self.update_contents.assert_not_called()

    def test_calls_update_contents_when_receiving_contents_start_and_end(self):
        for message in (
            UPDATE_START_PREFIX + '|15|First part of a',
            UPDATE_END_PREFIX + '|16| longer message.',
        ):
            self.handler.process(message)

        self.update_contents.assert_called_with('First part of a longer message.')

    def test_calls_update_contents_once_when_receiving_matching_end(self):
        for message in (
            UPDATE_START_PREFIX + '|15|First part of a',
            UPDATE_END_PREFIX + '|16| longer message.',
            UPDATE_END_PREFIX + '|16| longer message.',
        ):
            self.handler.process(message)

        self.update_contents.assert_called_once_with(
            'First part of a longer message.'
        )

    def test_calls_update_contents_once_for_matching_start_and_end(self):
        for message in (
            UPDATE_START_PREFIX + '|15|Not a part of a',
            UPDATE_START_PREFIX + '|15|First part of a',
            UPDATE_END_PREFIX + '|16| longer message.',
        ):
            self.handler.process(message)

        self.update_contents.assert_called_once_with(
            'First part of a longer message.'
        )

    def test_parts_between_start_and_end_can_extend_message(self):
        for message in (
            UPDATE_START_PREFIX + '|2|1 ',
            UPDATE_PART_PREFIX + '|2|2 ',
            UPDATE_END_PREFIX + '|1|3',
        ):
            self.handler.process(message)

        self.update_contents.assert_called_once_with('1 2 3')

    def test_does_not_call_update_contents_for_part_and_end_without_start(self):
        for message in (
            UPDATE_PART_PREFIX + '|2|2 ',
            UPDATE_END_PREFIX + '|1|3',
        ):
            self.handler.process(message)

        self.update_contents.assert_not_called()

    @data(
        TC('full_update', interrupting_message=FULL_UPDATE_PREFIX + '|5|Short'),
        TC('cursor',      interrupting_message=CURSOR_POSITION_PREFIX + '|1|1'),
        TC('malformed',   interrupting_message='%^' + UPDATE_PART_PREFIX + '@'),
    )
    def test_does_not_call_update_contents_if_other_message_received_before_end(
        self,
        context,
    ):
        for message in (
            UPDATE_START_PREFIX + '|2|1 ',
            UPDATE_PART_PREFIX + '|2|2 ',
            context.interrupting_message,
        ):
            self.handler.process(message)
        self.update_contents.reset_mock()

        self.handler.process(UPDATE_END_PREFIX + '|1|3')

        self.update_contents.assert_not_called()
