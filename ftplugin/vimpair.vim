python << EOF
import sys, os, vim
script_path = vim.eval('expand("<sfile>:p:h")')
python_path = os.path.abspath(os.path.join(script_path, 'python'))

if not python_path in sys.path:
  sys.path.append(python_path)


from functools import partial

from connection import (
  create_client_socket,
  create_server_socket,
)
from connectors import ClientConnector, ServerConnector
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

connector = None
message_handler = None


def show_status_message(message):
  if int(vim.eval('g:VimpairShowStatusMessages')) != 0:
    print 'Vimpair:', message

def send_message(message):
  if connector.connection:
    connector.connection.send_message(message)

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
  if connector.connection:
    for message in connector.connection.received_messages:
      message_handler.process(message)

def handle_take_control():
  show_status_message('You are in control now!')
  vim.command('call _VimpairStopTimer()')
  vim.command('call _VimpairStartObserving()')

def hand_over_control():
  show_status_message('Handing over control')
  vim.command('call _VimpairStopObserving()')
  send_message(generate_take_control_message())
  vim.command('call _VimpairStartTimer()')
EOF


let g:VimpairShowStatusMessages = 1
let g:VimpairTimerInterval = 200


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

function! _VimpairStartTimer()
  let g:_VimpairTimer = timer_start(
        \  g:VimpairTimerInterval,
        \  {-> execute("python process_messages()", "")},
        \  {'repeat': -1}
        \)
endfunction

function! _VimpairStopTimer()
  if g:_VimpairTimer != ""
    call timer_stop(g:_VimpairTimer)
    let g:_VimpairTimer = ""
  endif
endfunction


function! _VimpairInitialize()
  augroup VimpairCleanup
    autocmd VimLeavePre * call s:VimpairCleanup()
  augroup END

  python message_handler = MessageHandler(
        \  update_contents=partial(apply_contents_update, vim=vim),
        \  apply_cursor_position=partial(apply_cursor_position, vim=vim),
        \  take_control=handle_take_control,
        \)
endfunction

function! _VimpairCleanup()
  call _VimpairStopTimer()
  call _VimpairStopObserving()

  augroup VimpairCleanup
    autocmd!
  augroup END

  python message_handler = None
  python connector.disconnect()
endfunction


function! VimpairServerStart()
  call _VimpairInitialize()

  python connector = ClientConnector(server_socket_factory)

  call _VimpairStartObserving()
endfunction

function! VimpairServerStop()
  call _VimpairCleanup()
endfunction


function! VimpairClientStart()
  call _VimpairInitialize()

  python connector = ServerConnector(client_socket_factory)

  call _VimpairStartTimer()
endfunction

function! VimpairClientStop()
  call _VimpairCleanup()
endfunction


function! VimpairHandover()
  python hand_over_control()
endfunction
