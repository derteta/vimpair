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
    generate_save_file_message,
    MessageHandler,
)
from session import Session
from vim_interface import (
    apply_contents_update,
    apply_cursor_position,
    get_current_contents,
    get_current_filename,
    get_current_path,
    get_cursor_position,
    switch_to_buffer,
)


session = None

server_socket_factory = create_server_socket
client_socket_factory = create_client_socket

connector = None
message_handler = None

_vim_int = lambda name: int(vim.eval(name))

class SendFileChange(object):

    enabled = True

    def __call__(self):
        if self.enabled:
            message = generate_file_change_message(
                get_current_filename(vim=vim),
                folderpath=get_current_path(vim=vim),
                conceal_path=_vim_int('g:VimpairConcealFilePaths') != 0,
            )
            connector.connection.send_message(message)
            update_contents_and_cursor()


def show_status_message(message):
    if _vim_int('g:VimpairShowStatusMessages') != 0:
        print 'Vimpair:', message


def send_contents_update():
    contents = get_current_contents(vim=vim)
    messages = generate_contents_update_messages(contents)
    for message in messages:
        connector.connection.send_message(message)

def send_cursor_position():
    line, column = get_cursor_position(vim=vim)
    connector.connection.send_message(generate_cursor_position_message(line, column))

def update_contents_and_cursor():
    send_contents_update()
    send_cursor_position()

def send_save_file():
    message = generate_save_file_message()
    connector.connection.send_message(message)

send_file_change = SendFileChange()


class VimCallbacks(object):

    def __init__(self, vim=None):
        self._vim = vim
        self.update_contents = partial(apply_contents_update, vim=vim)
        self.apply_cursor_position = partial(apply_cursor_position, vim=vim)

    def take_control(self):
        show_status_message('You are in control now!')
        self._vim.command('call s:VimpairStopTimer()')
        self._vim.command('call s:VimpairStartObserving()')

    def file_changed(self, filename=None):
        switch_to_buffer(session.prepend_folder(filename), vim=self._vim)

    def save_file(self):
        filename = get_current_filename(vim=self._vim)
        if filename:
            path = get_current_path(vim=self._vim)
            os.makedirs(path)
            filename_and_path = os.path.join(path, filename)
            show_status_message('Saving file "%s"' % filename_and_path)
            self._vim.command('silent write! ' + filename_and_path)

EOF


let g:VimpairShowStatusMessages = 1
let g:VimpairConcealFilePaths = 1
let g:VimpairTimerInterval = 200


function! s:VimpairStartObserving()
  augroup VimpairEditorObservers
    autocmd TextChanged * python send_contents_update()
    autocmd TextChangedI * python send_contents_update()
    autocmd InsertLeave * python update_contents_and_cursor()
    autocmd CursorMoved * python send_cursor_position()
    autocmd CursorMovedI * python send_cursor_position()
    autocmd BufEnter * python send_file_change()
    autocmd BufWritePost * python send_save_file()
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
        \  "    connector.connection.received_messages" .
        \  ")"
        \)
endfunction


function! s:VimpairInitialize()
  augroup VimpairCleanup
    autocmd VimLeavePre * call s:VimpairCleanup()
  augroup END

  python message_handler = MessageHandler(callbacks=VimCallbacks(vim=vim))
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
endfunction

function! VimpairServerStop()
  call s:VimpairCleanup()
endfunction


function! VimpairClientStart()
  call s:VimpairInitialize()

  python connector = ServerConnector(client_socket_factory)

  python send_file_change.enabled = False
  python session = Session()
  call s:VimpairStartReceivingMessagesTimer()
endfunction

function! VimpairClientStop()
  call s:VimpairCleanup()
  python session.end()
endfunction


function! VimpairHandover()
  python show_status_message('Handing over control')
  call s:VimpairStopObserving()
  python connector.connection.send_message(generate_take_control_message())
  call s:VimpairStartReceivingMessagesTimer()
endfunction


command! -nargs=0 VimpairServerStart :call VimpairServerStart()
command! -nargs=0 VimpairServerStop :call VimpairServerStop()
command! -nargs=0 VimpairClientStart :call VimpairClientStart()
command! -nargs=0 VimpairClientStop :call VimpairClientStop()
command! -nargs=0 VimpairHandover :call VimpairHandover()
