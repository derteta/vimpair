python from mock import Mock
execute("source " . expand("<sfile>:p:h") . "/../vimpair.vim")


function! _VPServerTest_set_up()
  execute("vnew")
  call VimpairServerStart()
  python fake_connection = Mock()
  python connections.append(fake_connection)
endfunction

function! _VPServerTest_tear_down()
  call VimpairServerStop()
  execute("q!")
endfunction

function! _VPServerTest_assert_has_sent_message(expected)
  let g:_VPServerTest_expected = a:expected
  python fake_connection.send_message.assert_any_call(
    \ vim.vars['_VPServerTest_expected'])
endfunction


function! VPServerTest_sends_buffer_contents_on_connection_1()
  execute("normal iThis is just some text")

  call _VPServerTest_assert_has_sent_message(
    \ "VIMPAIR_FULL_UPDATE|22|This is just some text")
endfunction

function! VPServerTest_sends_buffer_contents_on_connection_2()
  execute("normal iThis is some other text")

  call _VPServerTest_assert_has_sent_message(
    \ "VIMPAIR_FULL_UPDATE|23|This is some other text")
endfunction

function! VPServerTest_sends_buffer_contents_on_connection_3()
  execute("normal iThis is line one")
  execute("normal oThis is line two")

  call _VPServerTest_assert_has_sent_message(
    \ "VIMPAIR_FULL_UPDATE|33|This is line one\nThis is line two")
endfunction

function! VPServerTest_sends_cursor_position_on_connection_1()
  execute("normal iThis is line one")
  execute("normal oThis is line two")
  execute("normal gg0ww")

  call VimpairServerUpdate()

  call _VPServerTest_assert_has_sent_message("VIMPAIR_CURSOR_POSITION|0|8")
endfunction

function! VPServerTest_sends_cursor_position_on_connection_2()
  execute("normal iThis is line one")
  execute("normal oThis is line two")
  execute("normal G0w")

  call VimpairServerUpdate()

  call _VPServerTest_assert_has_sent_message("VIMPAIR_CURSOR_POSITION|1|5")
endfunction


for Test in [
  \ function("VPServerTest_sends_buffer_contents_on_connection_1"),
  \ function("VPServerTest_sends_buffer_contents_on_connection_2"),
  \ function("VPServerTest_sends_buffer_contents_on_connection_3"),
  \ function("VPServerTest_sends_cursor_position_on_connection_1"),
  \ function("VPServerTest_sends_cursor_position_on_connection_2")]
  call _VPServerTest_set_up()
  call Test()
  call _VPServerTest_tear_down()
endfor
