from connection import Connection


class ClientConnector(object):

  def __init__(self, socket_factory):
    super(ClientConnector, self).__init__()
    self._connection = None
    self._server_socket = socket_factory()
    if self._server_socket:
      self._check_for_new_connection_to_client()

  def _check_for_new_connection_to_client(self):
    connection_socket, _ = self._server_socket.accept() \
      if self._server_socket \
      else (None, '')
    if connection_socket:
      self._connection = Connection(connection_socket)

  def disconnect(self):
    if self._connection:
      self._connection.close()
      self._connection = None

    if self._server_socket:
      self._server_socket.close()
      self._server_socket = None

  @property
  def connection(self):
    return self._connection


class ServerConnector(object):

  def __init__(self, socket_factory):
    super(ServerConnector, self).__init__()
    self._connection = None
    self._check_for_connection_to_server(socket_factory)

  def _check_for_connection_to_server(self, socket_factory):
    connection_socket = socket_factory()
    if connection_socket:
      self._connection = Connection(connection_socket)

  def disconnect(self):
    if self._connection is not None:
      self._connection.close()
      self._connection = None

  @property
  def connection(self):
    return self._connection
