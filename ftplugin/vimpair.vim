python << EOF
import sys, os, vim
script_path = vim.eval('expand("<sfile>:p:h")')
python_path = os.path.abspath(os.path.join(script_path, 'python'))

if not python_path in sys.path:
  sys.path.append(python_path)


from functools import partial

from connection import (
  Connection,
  create_client_socket,
  create_server_socket,
)
from protocol import (
  generate_contents_update_messages,
  generate_cursor_position_message,
  generate_take_control_message,
  MessageHandler,
)
from vim_interface import (
  apply_contents_update,
  apply_cursor_position,
  get_current_contents,
  get_cursor_position,
)


server_socket_factory = create_server_socket
client_socket_factory = create_client_socket

client_connector = None
server_connector = None
message_handler = None
current_connection = None


class ClientConnector(object):

  def __init__(self):
    super(ClientConnector, self).__init__()
    self._connection = None
    self._server_socket = server_socket_factory()
    if self._server_socket:
      self._check_for_new_connection_to_client()

  def _check_for_new_connection_to_client(self):
    global current_connection
    assert current_connection is None

    connection_socket, _ = self._server_socket.accept() \
      if self._server_socket \
      else (None, '')
    if connection_socket:
      self._connection = Connection(connection_socket)
      current_connection = self._connection

  def disconnect(self):
    global current_connection
    assert current_connection is self._connection

    if self._connection:
      self._connection.close()
      self._connection = None
      current_connection = None

    if self._server_socket:
      self._server_socket.close()
      self._server_socket = None


class ServerConnector(object):

  def __init__(self):
    super(ServerConnector, self).__init__()
    self._connection = None
    self._check_for_connection_to_server()

  def _check_for_connection_to_server(self):
    global current_connection
    assert current_connection is None

    connection_socket = client_socket_factory()
    if connection_socket:
      self._connection = Connection(connection_socket)
      current_connection = self._connection

  def disconnect(self):
    global current_connection
    assert current_connection is self._connection

    if self._connection is not None:
      self._connection.close()
      self._connection = None
      current_connection = None


def send_message(message):
  if current_connection:
    current_connection.send_message(message)

def send_contents_update():
  contents = get_current_contents(vim=vim)
  messages = generate_contents_update_messages(contents)
  for message in messages:
    send_message(message)

def send_cursor_position():
  line, column = get_cursor_position(vim=vim)
  send_message(generate_cursor_position_message(line, column))

def update_contents_and_cursor():
  send_contents_update()
  send_cursor_position()

def process_messages():
  if current_connection:
    for message in current_connection.received_messages:
      message_handler.process(message)

def handle_take_control():
  vim.command('call _VimpairStopTimer()')
  vim.command('call _VimpairStartObserving()')

def hand_over_control():
  vim.command('call _VimpairStopObserving()')
  send_message(generate_take_control_message())

message_handler_factory = lambda : MessageHandler(
  update_contents=partial(apply_contents_update, vim=vim),
  apply_cursor_position=partial(apply_cursor_position, vim=vim),
  take_control=handle_take_control,
)
EOF


function! _VimpairStartObserving()
  augroup VimpairEditorObservers
    autocmd TextChanged * python send_contents_update()
    autocmd TextChangedI * python send_contents_update()
    autocmd InsertLeave * python update_contents_and_cursor()
    autocmd CursorMoved * python send_cursor_position()
    autocmd CursorMovedI * python send_cursor_position()
  augroup END
endfunction

function! _VimpairStopObserving()
  augroup VimpairEditorObservers
    autocmd!
  augroup END
endfunction


let g:_VimpairTimer = ""

function! _VimpairStartTimer(func)
  let g:_VimpairTimer = timer_start(200, a:func, {'repeat': -1})
endfunction

function! _VimpairStopTimer()
  if g:_VimpairTimer != ""
    call timer_stop(g:_VimpairTimer)
    let g:_VimpairTimer = ""
  endif
endfunction


function! VimpairServerStart()
  augroup VimpairServer
    autocmd VimLeavePre * call VimpairServerStop()
  augroup END

  python client_connector = ClientConnector()

  call _VimpairStartObserving()
endfunction

function! VimpairServerStop()
  augroup VimpairServer
    autocmd!
  augroup END

  call _VimpairStopObserving()

  python client_connector.disconnect()
endfunction


function! VimpairClientStart()
  python server_connector = ServerConnector()
  python message_handler = message_handler_factory()

  augroup VimpairClient
    autocmd VimLeavePre * call VimpairClientStop()
  augroup END

  call _VimpairStartTimer('VimpairClientUpdate')
endfunction

function! VimpairClientStop()
  call _VimpairStopTimer()
  call _VimpairStopObserving()

  augroup VimpairClient
    autocmd!
  augroup END

  python message_handler = None
  python server_connector.disconnect()
endfunction

function! VimpairClientUpdate(timer)
  python process_messages()
endfunction


function! VimpairHandover()
  python hand_over_control()
endfunction
