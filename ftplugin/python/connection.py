from socket import (
    AF_INET,
    SOCK_STREAM,
    SOL_SOCKET,
    SO_REUSEADDR,
    error,
    gethostbyname,
    socket,
)


SERVER_ADDRESS = gethostbyname('localhost')
SERVER_PORT = 50007
MAX_READ_SIZE = 1024

_noop = lambda *a, **k: None


def create_server_socket():
    try:
        sock = socket(AF_INET, SOCK_STREAM)
        sock.settimeout(10.)
        sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        sock.bind((SERVER_ADDRESS, SERVER_PORT))
        sock.listen(1)
    except:
        sock.close()
        sock = None
    finally:
        return sock


def create_client_socket():
    try:
        sock = socket(AF_INET, SOCK_STREAM)
        sock.settimeout(.1)
        sock.connect((SERVER_ADDRESS, SERVER_PORT))
    except Exception as e:
        print str(e)
        sock.close()
        sock = None
    finally:
        return sock


class NullSocket(object):

    close = _noop
    sendall = _noop
    recv = _noop


class Connection(object):

    def __init__(self, socket):
        self._socket = socket or NullSocket()

    def close(self):
        self._socket.close()
        self._socket = NullSocket()

    def send_message(self, message):
        try:
            self._socket.sendall(message)
        except error as e:
            if e.errno == 32: # Broken pipe
                self.close()

    @property
    def received_messages(self):
        message = ''
        try:
            while True:
                new_part = self._socket.recv(MAX_READ_SIZE)
                if new_part:
                    message += new_part
                else:
                    # Broken connection?
                    break
        finally:
            return [message]
