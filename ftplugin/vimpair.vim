python << EOF
import vim

connections = []

def send_contents_update():
  content = reduce(lambda l1, l2: l1 + '\n' + l2, vim.current.buffer)
  message = 'VIMPAIR_FULL_UPDATE|%d|%s' % (len(content), content)
  for connection in connections:
    connection.send_message(message)

def send_cursor_position():
  # Vim counts lines 1-based, but columns are 0-based. Unifying.
  line, column = vim.current.window.cursor
  message = 'VIMPAIR_CURSOR_POSITION|%d|%d' % (line - 1, column)
  for connection in connections:
    connection.send_message(message)

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
