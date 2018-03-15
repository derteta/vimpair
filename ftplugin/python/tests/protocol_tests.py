from unittest import TestCase

from ..protocol import FULL_UPDATE_PREFIX, generate_contents_update_message


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
