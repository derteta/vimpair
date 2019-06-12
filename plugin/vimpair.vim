python << EOF
import sys, os, vim
script_path = vim.eval('expand("<sfile>:p:h")')
python_path = os.path.abspath(os.path.join(script_path, '..', 'python', 'vimpair'))

if not python_path in sys.path:
    sys.path.append(python_path)

import vimpair
from connection import (
    create_client_socket,
    create_server_socket,
)
from connectors import ClientConnector, ServerConnector
from protocol import MessageHandler
from session import Session

vimpair.vim = vim

server_socket_factory = create_server_socket
client_socket_factory = create_client_socket

session = None
message_handler = None

EOF


let g:VimpairShowStatusMessages = 1
let g:VimpairConcealFilePaths = 1
let g:VimpairTimerInterval = 200


function! s:VimpairStartObserving()
  augroup VimpairEditorObservers
    autocmd TextChanged * python vimpair.send_contents_update()
    autocmd TextChangedI * python vimpair.send_contents_update()
    autocmd InsertLeave * python vimpair.update_contents_and_cursor()
    autocmd CursorMoved * python vimpair.send_cursor_position()
    autocmd CursorMovedI * python vimpair.send_cursor_position()
    autocmd BufEnter * python vimpair.send_file_change()
    autocmd BufWritePost * python vimpair.send_file_change() ; vimpair.send_save_file()
  augroup END
endfunction

function! s:VimpairStopObserving()
  augroup VimpairEditorObservers
    autocmd!
  augroup END
endfunction


let s:VimpairTimer = ""

function! s:VimpairStartTimer(timer_command)
  let s:VimpairTimer = timer_start(
        \  g:VimpairTimerInterval,
        \  {-> execute(a:timer_command, "")},
        \  {'repeat': -1}
        \)
endfunction

function! s:VimpairStopTimer()
  if s:VimpairTimer != ""
    call timer_stop(s:VimpairTimer)
    let s:VimpairTimer = ""
  endif
endfunction


function! s:VimpairStartReceivingMessagesTimer()
  call s:VimpairStartTimer(
        \  "python message_handler.process(" .
        \  "    vimpair.connector.connection.received_messages" .
        \  ")"
        \)
endfunction

function! s:VimpairStartCheckingForClientTimer()
  call s:VimpairStartTimer("python vimpair.check_for_new_client()")
endfunction


function! s:VimpairInitialize()
  augroup VimpairCleanup
    autocmd VimLeavePre * call s:VimpairCleanup()
  augroup END

  python message_handler =
        \ MessageHandler(callbacks=vimpair.VimCallbacks(vim=vim, session=session))
endfunction

function! s:VimpairCleanup()
  call s:VimpairStopTimer()
  call s:VimpairStopObserving()

  augroup VimpairCleanup
    autocmd!
  augroup END

  python message_handler = None
  python vimpair.connector.disconnect()
endfunction


function! VimpairServerStart()
  call s:VimpairInitialize()

  python vimpair.connector = ClientConnector(server_socket_factory)

  call s:VimpairStartCheckingForClientTimer()
  call s:VimpairStartObserving()
  python vimpair.send_file_change.enabled = True
  python vimpair.send_file_change()
endfunction

function! VimpairServerStop()
  call s:VimpairCleanup()
endfunction


function! VimpairClientStart()
  python session = Session()
  call s:VimpairInitialize()

  python vimpair.connector = ServerConnector(client_socket_factory)

  python vimpair.send_file_change.enabled = False
  call s:VimpairStartReceivingMessagesTimer()
endfunction

function! VimpairClientStop()
  call s:VimpairCleanup()
  python session.end()
  python session = None
endfunction


function! VimpairHandover()
  python vimpair.hand_over_control()
endfunction


command! -nargs=0 VimpairServerStart :call VimpairServerStart()
command! -nargs=0 VimpairServerStop :call VimpairServerStop()
command! -nargs=0 VimpairClientStart :call VimpairClientStart()
command! -nargs=0 VimpairClientStop :call VimpairClientStop()
command! -nargs=0 VimpairHandover :call VimpairHandover()
