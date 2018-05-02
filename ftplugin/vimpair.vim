python << EOF
import sys, os, vim
script_path = vim.eval('expand("<sfile>:p:h")')
python_path = os.path.abspath(os.path.join(script_path, 'python'))

if not python_path in sys.path:
  sys.path.append(python_path)

from functools import partial

from connection import Connection
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


server_socket_factory = lambda: None
client_socket_factory = lambda: None
connections = []
server_socket = None
message_handler = None

def check_for_new_connection_to_client():
  global connections
  connection_socket, _ = server_socket.accept() \
    if server_socket \
    else (None, '')
  if connection_socket:
    connections.append(Connection(connection_socket))

def check_for_connection_to_server():
  global connections
  connection_socket = client_socket_factory()
  if connection_socket:
    connections.append(Connection(connection_socket))

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

let g:_VimpairClientTimer = ""


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

check_for_new_connection_to_client()
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

check_for_connection_to_server()
EOF
  let g:_VimpairClientTimer = timer_start(
        \ 200,
        \ 'VimpairClientUpdate',
        \ {'repeat': -1})
endfunction

function! VimpairClientStop()
  if g:_VimpairClientTimer != ""
    call timer_stop(g:_VimpairClientTimer)
    let g:_VimpairClientTimer = ""
  endif
  python connections = None
  python message_handler = None
endfunction

function! VimpairClientUpdate(timer)
  python process_messages()
endfunction
