from connection import Connection
from threading import Thread, Lock


class ConnectionHolder(object):

    def __init__(self):
        self._setup_connection(None)

    def _setup_connection(self, socket):
        self._connection = Connection(socket)

    @property
    def connection(self):
        return self._connection

    def disconnect(self):
        self._connection.close()
        self._setup_connection(None)


class ClientConnector(ConnectionHolder):

    def __init__(self, socket_factory):
        self._lock = Lock()

        super(ClientConnector, self).__init__()
        self._server_socket = socket_factory()

        self._start_waiting_for_client()

    @property
    def is_waiting_for_connection(self):
        return self._wait_for_client

    def _start_waiting_for_client(self):
        self._wait_for_client = True
        self._thread = Thread(target=self._check_for_new_connection_to_client)
        self._thread.start()

    def _stop_waiting_for_client(self):
        self._wait_for_client = False
        self._thread.join()

    def _check_for_new_connection_to_client(self):
        if self._server_socket:
            while self._wait_for_client:
                connection_socket = self._server_socket.get_client_connection()
                if connection_socket:
                    self._setup_connection(connection_socket)
                    self._wait_for_client = False

    def _setup_connection(self, socket):
        with self._lock:
            super(ClientConnector, self)._setup_connection(socket)

    @property
    def connection(self):
        with self._lock:
            return self._connection

    def disconnect(self):
        self._stop_waiting_for_client()

        super(ClientConnector, self).disconnect()

        if self._server_socket:
            self._server_socket.close()
            self._server_socket = None


class SingleThreadedClientConnector(ClientConnector):

    def _start_waiting_for_client(self):
        self._wait_for_client = True
        self._check_for_new_connection_to_client()

    def _stop_waiting_for_client(self):
        self._wait_for_client = False

    def set_waiting_for_connection(self, waiting):
        self._wait_for_client = waiting


class ServerConnector(ConnectionHolder):

    def __init__(self, socket_factory):
        super(ServerConnector, self).__init__()
        self._check_for_connection_to_server(socket_factory)

    def _check_for_connection_to_server(self, socket_factory):
        connection_socket = socket_factory()
        self._setup_connection(connection_socket)
