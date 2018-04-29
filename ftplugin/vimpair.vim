python << EOF
import sys, os, vim
script_path = vim.eval('expand("<sfile>:p:h")')
python_path = os.path.abspath(os.path.join(script_path, 'python'))

if not python_path in sys.path:
  sys.path.append(python_path)

from functools import partial

from protocol import (
  generate_contents_update_messages,
  generate_cursor_position_message,
  MessageHandler,
)
from vim_interface import (
  apply_contents_update,
  apply_cursor_position,
  get_current_contents,
  get_cursor_position,
)


class Connection(object):

  def __init__(self, socket):
    self._socket = socket
    self.close = socket.close

  def send_message(self, message):
    self._socket.sendall(message)

  @property
  def received_messages(self):
    messages = []
    try:
      while True:
        new_message = self._socket.recv(1024)
        messages.append(new_message)
    finally:
      return messages


server_socket_factory = lambda: None
client_socket_factory = lambda: None
connections = []
server_socket = None
message_handler = None

def get_connection_to_client():
  connection_socket, _  = server_socket.accept() \
    if server_socket \
    else (None, '')
  return Connection(connection_socket) if connection_socket else None

def get_connection_to_server():
  connection_socket = client_socket_factory()
  return Connection(connection_socket) if connection_socket else None

def send_contents_update():
  contents = get_current_contents(vim=vim)
  messages = generate_contents_update_messages(contents)
  for connection in connections:
    for message in messages:
      connection.send_message(message)

def send_cursor_position():
  line, column = get_cursor_position(vim=vim)
  message = generate_cursor_position_message(line, column)
  for connection in connections:
    connection.send_message(message)

def process_messages():
  if connections:
    for message in connections[0].received_messages:
      message_handler.process(message)

EOF


function! VimpairServerStart()
  augroup VimpairServer
    autocmd TextChanged * python send_contents_update()
    autocmd TextChangedI * python send_contents_update()
    autocmd InsertLeave * call VimpairServerUpdate()
    autocmd CursorMoved * python send_cursor_position()
    autocmd CursorMovedI * python send_cursor_position()
  augroup END

python << EOF
connections = []
server_socket = server_socket_factory()

new_connection = get_connection_to_client()
if new_connection:
  connections.append(new_connection)
EOF
endfunction

function! VimpairServerStop()
python << EOF
for connection in connections:
  connection.close()
connections = None

if server_socket:
  server_socket.close()
  server_socket = None
EOF

  augroup VimpairServer
    autocmd!
  augroup END
endfunction

function! VimpairServerUpdate()
  python send_contents_update()
  python send_cursor_position()
endfunction


function! VimpairClientStart()
python << EOF
connections = []
message_handler = MessageHandler(
  update_contents=partial(apply_contents_update, vim=vim),
  apply_cursor_position=partial(apply_cursor_position, vim=vim),
)
new_connection = get_connection_to_server()
if new_connection:
  connections.append(new_connection)
EOF
endfunction

function! VimpairClientStop()
  python connections = None
  python message_handler = None
endfunction

function! VimpairClientUpdate()
  python process_messages()
endfunction
