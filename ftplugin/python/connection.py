from socket import (
    AF_INET,
    SOCK_STREAM,
    SOL_SOCKET,
    SO_REUSEADDR,
    gethostbyname,
    gethostname,
    socket,
)


SERVER_ADDRESS = gethostbyname(gethostname())
SERVER_PORT = 50007
MAX_READ_SIZE = 1024


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


class Connection(object):

    def __init__(self, socket):
        self.close = socket.close
        self.send_message = socket.sendall
        self._socket = socket

    @property
    def received_messages(self):
        message = ''
        try:
            while True:
                new_part = self._socket.recv(MAX_READ_SIZE)
                message += new_part
                if not new_part:
                    # Broken connection?
                    break
        finally:
            return [message]
