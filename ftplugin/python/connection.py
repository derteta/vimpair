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
                message += self._socket.recv(1024)
        finally:
            return [message]
