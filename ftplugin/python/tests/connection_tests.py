from functools import partial
from mock import Mock
from socket import timeout
from unittest import TestCase

from ..connection import Connection

def fake_recv(_number_of_bytes, values=[]):
    if len(values) == 0:
        raise timeout
    return values.pop()


class ConnectionTests(TestCase):

    def setUp(self):
        self.socket = Mock()
        self.connection = Connection(self.socket)


    def test_closing_connection_calls_close_on_socket(self):
        self.connection.close()

        self.socket.close.assert_called()

    def test_send_message_forwards_message_to_sendall(self):
        self.connection.send_message('Some message')

        self.socket.sendall.assert_called_with('Some message')

    def test_received_messages_contain_single_message_from_recv(self):
        self.socket.recv = partial(fake_recv, values=['Some message'])

        self.assertEqual(['Some message'], self.connection.received_messages)

    def test_received_messages_concatenate_all_messages_until_timeout(self):
        self.socket.recv = partial(
            fake_recv,
            values=['Another message', 'Some message']
        )

        self.assertEqual(
            ['Some messageAnother message'],
            self.connection.received_messages,
        )
