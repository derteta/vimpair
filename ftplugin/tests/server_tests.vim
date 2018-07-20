python from mock import call, Mock
execute("source " . expand("<sfile>:p:h") . "/test_tools.vim")
execute("source " . expand("<sfile>:p:h") . "/../vimpair.vim")


function! _VPServerTest_set_up()
  execute("vnew")
  python fake_socket = Mock()
  python server_socket = Mock()
  python server_socket.accept = Mock(return_value=(fake_socket, ''))
  python server_socket_factory = lambda: server_socket
  call VimpairServerStart()
endfunction

function! _VPServerTest_tear_down()
  call VimpairServerStop()
  execute("q!")
endfunction

function! _VPServerTest_assert_has_sent_message(expected)
  python fake_socket.sendall.assert_any_call(
    \ vim.eval('a:expected'))
endfunction

function! _VPServerTest_assert_has_not_sent_message(expected)
  python sendall_calls = fake_socket.sendall.call_args_list
  python assert not call(vim.eval('a:expected')) in sendall_calls
endfunction

function! _VPServerTest_assert_buffer_has_contents(expected)
python << EOF
actual = list(vim.current.buffer)
expected = list(vim.eval('a:expected'))
assert actual == expected, actual
EOF
endfunction

function! _VPServerTest_wait_for_timer()
  sleep 300m
endfunction


function! VPServerTest_sends_buffer_contents_on_connection()
  execute("normal iThis is just some text")

  call _VPServerTest_assert_has_sent_message(
    \ "VIMPAIR_FULL_UPDATE|22|This is just some text")
endfunction

function! VPServerTest_sends_cursor_position_on_connection()
  execute("normal iThis is line one")
  execute("normal oThis is line two")

  execute("normal gg0ww")
  " The CursorMoved autocommand is not reported in this scope,
  " so we need to manually trigger it
  execute("doautocmd CursorMoved")

  call _VPServerTest_assert_has_sent_message("VIMPAIR_CURSOR_POSITION|0|8")
endfunction

function! VPServerTest_sends_long_buffer_contents_in_chunks()
  execute("normal a0123456789")
  execute("normal 201.")

  call _VPServerTest_assert_has_sent_message(
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
  call _VPServerTest_assert_has_sent_message(
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
  call _VPServerTest_assert_has_sent_message(
    \ "VIMPAIR_CONTENTS_END|25|5678901234567890123456789")
endfunction

function! VPServerTest_sends_buffer_contents_on_copy_paste()
  execute("normal iThis is just some text")

  execute("normal yyp")
  execute("doautocmd TextChanged")

  call _VPServerTest_assert_has_sent_message(
    \ "VIMPAIR_FULL_UPDATE|45|This is just some text\nThis is just some text")
endfunction

function! VPServerTest_sends_take_control_message_for_handover()
  call VimpairHandover()

  call _VPServerTest_assert_has_sent_message("VIMPAIR_TAKE_CONTROL")
endfunction

function! VPServerTest_does_not_send_updates_after_handover()
  call VimpairHandover()

  execute("normal iThis is just some text")

  call _VPServerTest_assert_has_not_sent_message(
    \ "VIMPAIR_FULL_UPDATE|22|This is just some text")
endfunction

function! VPServerTest_applies_received_updates_after_handover()
  call VimpairHandover()
  python received_messages = ["VIMPAIR_FULL_UPDATE|16|This is line one"]
  python fake_socket.recv = lambda *a: received_messages.pop()

  call _VPServerTest_wait_for_timer()

  call _VPServerTest_assert_buffer_has_contents(["This is line one"])
endfunction


call VPTestTools_run_tests("VPServerTest")
