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
  generate_file_change_message,
  generate_take_control_message,
  MessageHandler,
)
from vim_interface import (
  apply_contents_update,
  apply_cursor_position,
  get_current_contents,
  get_current_filename,
  get_cursor_position,
  switch_to_buffer,
)


server_socket_factory = create_server_socket
client_socket_factory = create_client_socket

connector = None
message_handler = None


class SendFileChange(object):

  enabled = True

  def __call__(self):
    if self.enabled:
      message = generate_file_change_message(get_current_filename(vim=vim))
      send_message(message)


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

send_file_change = SendFileChange()

def process_messages():
  if connector.connection:
    for message in connector.connection.received_messages:
      message_handler.process(message)

def handle_take_control():
  show_status_message('You are in control now!')
  vim.command('call s:VimpairStopTimer()')
  vim.command('call s:VimpairStartObserving()')

def hand_over_control():
  show_status_message('Handing over control')
  vim.command('call s:VimpairStopObserving()')
  send_message(generate_take_control_message())
  vim.command('call s:VimpairStartTimer()')


class VimCallbacks(object):

    update_contents=partial(apply_contents_update, vim=vim)
EOF


let g:VimpairShowStatusMessages = 1
let g:VimpairTimerInterval = 200


function! s:VimpairStartObserving()
  augroup VimpairEditorObservers
    autocmd TextChanged * python send_contents_update()
    autocmd TextChangedI * python send_contents_update()
    autocmd InsertLeave * python update_contents_and_cursor()
    autocmd CursorMoved * python send_cursor_position()
    autocmd CursorMovedI * python send_cursor_position()
    autocmd BufEnter * python send_file_change()
  augroup END
endfunction

function! s:VimpairStopObserving()
  augroup VimpairEditorObservers
    autocmd!
  augroup END
endfunction


let s:VimpairTimer = ""

function! s:VimpairStartTimer()
  let s:VimpairTimer = timer_start(
        \  g:VimpairTimerInterval,
        \  {-> execute("python process_messages()", "")},
        \  {'repeat': -1}
        \)
endfunction

function! s:VimpairStopTimer()
  if s:VimpairTimer != ""
    call timer_stop(s:VimpairTimer)
    let s:VimpairTimer = ""
  endif
endfunction


function! s:VimpairInitialize()
  augroup VimpairCleanup
    autocmd VimLeavePre * call s:VimpairCleanup()
  augroup END

  python message_handler = MessageHandler(
        \  callbacks=VimCallbacks,
        \  apply_cursor_position=partial(apply_cursor_position, vim=vim),
        \  take_control=handle_take_control,
        \  file_changed=partial(switch_to_buffer, vim=vim),
        \)
endfunction

function! s:VimpairCleanup()
  call s:VimpairStopTimer()
  call s:VimpairStopObserving()

  augroup VimpairCleanup
    autocmd!
  augroup END

  python message_handler = None
  python connector.disconnect()
endfunction


function! VimpairServerStart()
  call s:VimpairInitialize()

  python connector = ClientConnector(server_socket_factory)

  call s:VimpairStartObserving()
  python send_file_change()
  python update_contents_and_cursor()
endfunction

function! VimpairServerStop()
  call s:VimpairCleanup()
endfunction


function! VimpairClientStart()
  call s:VimpairInitialize()

  python connector = ServerConnector(client_socket_factory)

  python send_file_change.enabled = False
  call s:VimpairStartTimer()
endfunction

function! VimpairClientStop()
  call s:VimpairCleanup()
endfunction


function! VimpairHandover()
  python hand_over_control()
endfunction


command! -nargs=0 VimpairServerStart :call VimpairServerStart()
command! -nargs=0 VimpairServerStop :call VimpairServerStop()
command! -nargs=0 VimpairClientStart :call VimpairClientStart()
command! -nargs=0 VimpairClientStop :call VimpairClientStop()
command! -nargs=0 VimpairHandover :call VimpairHandover()
