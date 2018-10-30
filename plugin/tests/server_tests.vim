python from mock import call, Mock
execute("source " . expand("<sfile>:p:h") . "/test_tools.vim")
execute("source " . expand("<sfile>:p:h") . "/../vimpair.vim")


python << EOF

class SingleThreadedClientConnector(ClientConnector):
    """
        For the pupose of the tests below, we set up a fake
        connection instantly. So we don't want to wait for
        a worker thread to pick it up
    """

    def _start_waiting_for_client(self):
        self._wait_for_client = True
        self._check_for_new_connection_to_client()

    def _stop_waiting_for_client(self):
        self._wait_for_client = False

    def set_waiting_for_connection(self, waiting):
        self._wait_for_client = waiting


ClientConnector = SingleThreadedClientConnector

EOF

let g:VimpairShowStatusMessages = 0
let g:VimpairConcealFilePaths = 0
let g:VimpairTimerInterval = 1

function! _VPServerTest_set_up()
  execute("vnew")
  python sendall_calls = []
  python fake_socket = Mock(sendall=lambda b: sendall_calls.append(b))
  python server_socket = Mock(get_client_connection=lambda : fake_socket)
  python server_socket_factory = lambda: server_socket
  VimpairServerStart
endfunction

function! _VPServerTest_tear_down()
  VimpairServerStop
  execute("q!")
endfunction

function! s:VPServerTest_assert_has_sent_message(expected)
  python expected_call = vim.eval('a:expected')
  python assert expected_call in sendall_calls,
        \ "Message was not sent: '%s'" % expected_call
  python del expected_call
endfunction

function! s:VPServerTest_assert_has_sent_message_starting_with(expected)
  python expected_call = vim.eval('a:expected')
  python assert any([c.startswith(expected_call) for c in sendall_calls]),
        \ "No Message sent starting with '%s'" % expected_call
  python del expected_call
endfunction

function! s:VPServerTest_assert_has_not_sent_message(unexpected)
  python unexpected_call = vim.eval('a:unexpected')
  python assert not unexpected_call in sendall_calls,
        \ "Sent message '%s', but should not have" % unexpected_call
  python del unexpected_call
endfunction

function! s:VPServerTest_assert_buffer_has_contents(expected)
python << EOF
actual = list(vim.current.buffer)
expected = list(vim.eval('a:expected'))
assert actual == expected, actual
EOF
endfunction

function! s:VPServerTest_wait_for_timer()
  sleep 3m
endfunction


function! VPServerTest_sends_buffer_contents_on_connection()
  call s:VPServerTest_assert_has_sent_message("VIMPAIR_FULL_UPDATE|0|")
endfunction

function! VPServerTest_sends_cursor_position_on_connection()
  call s:VPServerTest_assert_has_sent_message("VIMPAIR_CURSOR_POSITION|0|0")
endfunction

function! VPServerTest_sends_file_change_on_connection()
  call s:VPServerTest_assert_has_sent_message("VIMPAIR_FILE_CHANGE|0|")
endfunction

function! VPServerTest_sends_buffer_contents_on_change()
  execute("normal iThis is just some text")

  call s:VPServerTest_assert_has_sent_message(
    \ "VIMPAIR_FULL_UPDATE|22|This is just some text")
endfunction

function! VPServerTest_sends_cursor_position_on_change()
  execute("normal iThis is line one")
  execute("normal oThis is line two")

  execute("normal gg0ww")
  " The CursorMoved autocommand is not reported in this scope,
  " so we need to manually trigger it
  execute("doautocmd CursorMoved")

  call s:VPServerTest_assert_has_sent_message("VIMPAIR_CURSOR_POSITION|0|8")
endfunction

function! VPServerTest_sends_long_buffer_contents_in_chunks()
  execute("normal a0123456789")
  execute("normal 201.")

  call s:VPServerTest_assert_has_sent_message(
    \ "VIMPAIR_CONTENTS_START|997|01234567890123456789012345678901234567890123"
    \ . "456789012345678901234567890123456789012345678901234567890123456789012"
    \ . "345678901234567890123456789012345678901234567890123456789012345678901"
    \ . "234567890123456789012345678901234567890123456789012345678901234567890"
    \ . "123456789012345678901234567890123456789012345678901234567890123456789"
    \ . "012345678901234567890123456789012345678901234567890123456789012345678"
    \ . "901234567890123456789012345678901234567890123456789012345678901234567"
    \ . "890123456789012345678901234567890123456789012345678901234567890123456"
    \ . "789012345678901234567890123456789012345678901234567890123456789012345"
    \ . "678901234567890123456789012345678901234567890123456789012345678901234"
    \ . "567890123456789012345678901234567890123456789012345678901234567890123"
    \ . "456789012345678901234567890123456789012345678901234567890123456789012"
    \ . "345678901234567890123456789012345678901234567890123456789012345678901"
    \ . "234567890123456789012345678901234567890123456789012345678901234567890"
    \ . "12345678901234567890123456789012345678901234567890123456")
  call s:VPServerTest_assert_has_sent_message(
    \ "VIMPAIR_CONTENTS_PART|998|789012345678901234567890123456789012345678901"
    \ . "234567890123456789012345678901234567890123456789012345678901234567890"
    \ . "123456789012345678901234567890123456789012345678901234567890123456789"
    \ . "012345678901234567890123456789012345678901234567890123456789012345678"
    \ . "901234567890123456789012345678901234567890123456789012345678901234567"
    \ . "890123456789012345678901234567890123456789012345678901234567890123456"
    \ . "789012345678901234567890123456789012345678901234567890123456789012345"
    \ . "678901234567890123456789012345678901234567890123456789012345678901234"
    \ . "567890123456789012345678901234567890123456789012345678901234567890123"
    \ . "456789012345678901234567890123456789012345678901234567890123456789012"
    \ . "345678901234567890123456789012345678901234567890123456789012345678901"
    \ . "234567890123456789012345678901234567890123456789012345678901234567890"
    \ . "123456789012345678901234567890123456789012345678901234567890123456789"
    \ . "012345678901234567890123456789012345678901234567890123456789012345678"
    \ . "90123456789012345678901234567890123456789012345678901234")
  call s:VPServerTest_assert_has_sent_message(
    \ "VIMPAIR_CONTENTS_END|25|5678901234567890123456789")
endfunction

function! VPServerTest_sends_buffer_contents_on_copy_paste()
  execute("normal iThis is just some text")

  execute("normal yyp")
  execute("doautocmd TextChanged")

  call s:VPServerTest_assert_has_sent_message(
    \ "VIMPAIR_FULL_UPDATE|45|This is just some text\nThis is just some text")
endfunction

function! VPServerTest_sends_take_control_message_for_handover()
  VimpairHandover

  call s:VPServerTest_assert_has_sent_message("VIMPAIR_TAKE_CONTROL")
endfunction

function! VPServerTest_does_not_send_updates_after_handover()
  VimpairHandover

  execute("normal iThis is just some text")

  call s:VPServerTest_assert_has_not_sent_message(
    \ "VIMPAIR_FULL_UPDATE|22|This is just some text")
endfunction

function! VPServerTest_applies_received_updates_after_handover()
  VimpairHandover
  python received_messages = ["VIMPAIR_FULL_UPDATE|16|This is line one"]
  python fake_socket.recv = lambda *a: received_messages.pop()

  call s:VPServerTest_wait_for_timer()

  call s:VPServerTest_assert_buffer_has_contents(["This is line one"])
endfunction

function! VPServerTest_sends_file_change_on_buffer_name_change()
  " Faking writing the buffer to disk with a new name, so we don't need to clean up
  python vim.current.buffer.name = "SomeRandomName"
  execute("doautocmd BufWritePost")

  let file_path = expand("%:p")
  call s:VPServerTest_assert_has_sent_message(
    \ "VIMPAIR_FILE_CHANGE|" . printf("%d", strlen(file_path)) . "|" . file_path)
endfunction

function! VPServerTest_sends_file_change_on_change()
  execute("silent e " . expand("%:p:h") . "/../README.md")

  let file_path = expand("%:p")
  call s:VPServerTest_assert_has_sent_message(
    \ "VIMPAIR_FILE_CHANGE|" . printf("%d", strlen(file_path)) . "|" . file_path)
endfunction

function! VPServerTest_sends_file_contents_on_file_change()
  python sendall_calls = []

  execute("silent e " . expand("%:p:h") . "/../.gitignore")

  call s:VPServerTest_assert_has_sent_message_starting_with(
    \ "VIMPAIR_FULL_UPDATE|")
endfunction

function! VPServerTest_sends_save_file_message_when_saving()
  execute("silent e " . expand("%:p:h") . "/../README.md")

  execute("silent w")

  call s:VPServerTest_assert_has_sent_message("VIMPAIR_SAVE_FILE")
endfunction

function! VPServerTest_doesnt_send_save_file_message_when_saving_after_handover()
  execute("silent e " . expand("%:p:h") . "/../README.md")
  VimpairHandover

  execute("silent w")

  call s:VPServerTest_assert_has_not_sent_message("VIMPAIR_SAVE_FILE")
endfunction

function! VPServerTest_doesnt_send_take_control_message_while_waiting_for_client()
  python connector.set_waiting_for_connection(True)

  VimpairHandover

  call s:VPServerTest_assert_has_not_sent_message("VIMPAIR_TAKE_CONTROL")
endfunction


call VPTestTools_run_tests("VPServerTest")
