from connection import Connection


class ConnectionHolder(object):

  _connection = None

  def _setup_connection(self, socket):
    if socket:
      self._connection = Connection(socket)

  @property
  def connection(self):
    return self._connection

  def disconnect(self):
    if self._connection:
      self._connection.close()
      self._connection = None


class ClientConnector(ConnectionHolder):

  def __init__(self, socket_factory):
    super(ClientConnector, self).__init__()
    self._server_socket = socket_factory()
    self._check_for_new_connection_to_client()

  def _check_for_new_connection_to_client(self):
    connection_socket, _ = self._server_socket.accept() \
      if self._server_socket \
      else (None, '')
    self._setup_connection(connection_socket)

  def disconnect(self):
    super(ClientConnector, self).disconnect()

    if self._server_socket:
      self._server_socket.close()
      self._server_socket = None


class ServerConnector(ConnectionHolder):

  def __init__(self, socket_factory):
    super(ServerConnector, self).__init__()
    self._check_for_connection_to_server(socket_factory)

  def _check_for_connection_to_server(self, socket_factory):
    connection_socket = socket_factory()
    self._setup_connection(connection_socket)
