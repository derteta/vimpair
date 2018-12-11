from functools import partial
from mock import Mock, patch
from socket import AF_INET, SOCK_STREAM, error, socket, timeout
from unittest import TestCase

from ..connection import Connection, create_client_socket

def fake_recv(_number_of_bytes, values=[]):
    if len(values) == 0:
        raise timeout
    return values.pop()

def raise_broken_pipe(*_):
    err = error()
    err.errno = 32
    raise err


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

    def test_closing_socket_on_broken_pipe(self):
        self.socket.sendall.side_effect = raise_broken_pipe

        self.connection.send_message('Some message')

        self.socket.close.assert_called()

    def test_sendall_not_called_again_after_broken_pipe(self):
        self.socket.sendall.side_effect = raise_broken_pipe
        self.connection.send_message('Some message')
        self.socket.sendall.reset_mock()

        self.connection.send_message('Another message')

        self.socket.sendall.assert_not_called()


class ClientSocketFactoryTests(TestCase):

    EXPECTED_PORT = 50007

    @patch('socket.socket.connect')
    def test_creates_internet_socket(self, _):
        client_socket = create_client_socket()

        self.assertEqual(client_socket.family, AF_INET)

    @patch('socket.socket.connect')
    def test_creates_stream_socket(self, _):
        client_socket = create_client_socket()

        self.assertEqual(client_socket.type, SOCK_STREAM)

    @patch('socket.socket.connect')
    def test_returns_None_if_exception_is_raised(self, mocked_connect):

        def raise_exception():
            raise Exception

        mocked_connect.side_effect = raise_exception

        self.assertEqual(create_client_socket(), None)

    @patch('socket.socket.connect')
    def test_connects_to_localhost_if_no_address_is_specified(self, mocked_connect):
        create_client_socket()

        mocked_connect.assert_called_with(('127.0.0.1', self.EXPECTED_PORT))
