python << EOF
import sys, os, vim
script_path = vim.eval('expand("<sfile>:p:h")')
python_path = os.path.abspath(os.path.join(script_path, 'python'))

if not python_path in sys.path:
  sys.path.append(python_path)

from vim_interface import (
  apply_contents_update,
  apply_cursor_position,
  get_current_contents,
  get_cursor_position,
)

connections = []

def send_contents_update():
  content = get_current_contents(vim=vim)
  message = 'VIMPAIR_FULL_UPDATE|%d|%s' % (len(content), content)
  for connection in connections:
    connection.send_message(message)

def send_cursor_position():
  message = 'VIMPAIR_CURSOR_POSITION|%d|%d' % get_cursor_position(vim=vim)
  for connection in connections:
    connection.send_message(message)

def process_messages():
  if connections:
    for message in connections[0].received_messages:
      if message.startswith('VIMPAIR_FULL_UPDATE'):
        contents = message[23:]
        apply_contents_update(contents, vim=vim)
      elif message.startswith('VIMPAIR_CURSOR_POSITION'):
        contents = message[24:]
        line, column = map(int, contents.split('|'))
        apply_cursor_position(line, column, vim=vim)

EOF

function! VimpairServerStart()
  augroup VimpairServer
    autocmd TextChanged * python send_contents_update()
    autocmd TextChangedI * python send_contents_update()
    autocmd InsertLeave * call VimpairServerUpdate()
    autocmd CursorMoved * python send_cursor_position()
    autocmd CursorMovedI * python send_cursor_position()
  augroup END

  python connections = []
endfunction

function! VimpairServerStop()
  python connections = None

  augroup VimpairServer
    autocmd!
  augroup END
endfunction

function! VimpairServerUpdate()
  python send_contents_update()
  python send_cursor_position()
endfunction

function! VimpairClientStart()
  python connections = []
endfunction

function! VimpairClientStop()
  python connections = None
endfunction

function! VimpairClientUpdate()
  python process_messages()
endfunction
