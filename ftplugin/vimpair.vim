python << EOF
import vim

connections = []

def send_contents_update():
  content = reduce(lambda l1, l2: l1 + '\n' + l2, vim.current.buffer)
  message = 'VIMPAIR_FULL_UPDATE|%d|%s' % (len(content), content)
  for connection in connections: connection.send_message(message)

EOF

function! VimpairServerStart()
  python connections = []
endfunction

function! VimpairServerStop()
  python connections = None
endfunction

function! VimpairServerUpdate()
  python send_contents_update()
endfunction
