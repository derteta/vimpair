python from mock import Mock
python import vim
execute("source " . expand("<sfile>:p:h") . "/test_tools.vim")
execute("source " . expand("<sfile>:p:h") . "/../vimpair.vim")


function! _VPClientTest_set_up()
  execute("vnew")
  call VimpairClientStart()
  python fake_connection = Mock()
  python connections.append(fake_connection)
endfunction

function! _VPClientTest_tear_down()
  call VimpairClientStop()
  execute("q!")
endfunction

function! _VPClientTest_assert_buffer_has_contents(expected)
  let g:_VPClientTest_expected = a:expected
  python actual = list(vim.current.buffer)
  python expected = list(vim.vars['_VPClientTest_expected'])
  python assert actual == expected, actual
endfunction


function! VPClientTest_applies_received_contents_updates_1()
  python fake_connection.received_messages =
        \ ["VIMPAIR_FULL_UPDATE|16|This is line one"]

  call VimpairClientUpdate()

  call _VPClientTest_assert_buffer_has_contents(["This is line one"])
endfunction

function! VPClientTest_applies_received_contents_updates_2()
  python fake_connection.received_messages =
        \ ["VIMPAIR_FULL_UPDATE|23|This is line one\nThis is line two"]

  call VimpairClientUpdate()

  call _VPClientTest_assert_buffer_has_contents(
        \ ["This is line one", "This is line two"])
endfunction

function! VPClientTest_received_contents_updates_overwrite_existing_contents()
  python fake_connection.received_messages =
        \ ["VIMPAIR_FULL_UPDATE|16|This is line one"]

  call VimpairClientUpdate()

  call _VPClientTest_assert_buffer_has_contents(["This is line one"])
endfunction

function! VPClientTest_applies_received_contents_updates_2()
  python fake_connection.received_messages =
        \ ["VIMPAIR_FULL_UPDATE|23|This is line one\nThis is line two"]

  call VimpairClientUpdate()

  call _VPClientTest_assert_buffer_has_contents(
        \ ["This is line one", "This is line two"])
endfunction

function! VPClientTest_received_contents_updates_overwrite_existing_contents()
  execute("normal i1")
  execute("normal o2")
  python fake_connection.received_messages =
        \ ["VIMPAIR_FULL_UPDATE|16|This is line one"]

  call VimpairClientUpdate()

  call _VPClientTest_assert_buffer_has_contents(["This is line one"])
endfunction

function! VPClientTest_received_cursor_position_is_applied()
  execute("normal iThis is line one")
  execute("normal oThis is line two")
  python fake_connection.received_messages = ["VIMPAIR_CURSOR_POSITION|0|8"]

  call VimpairClientUpdate()

  python assert vim.current.window.cursor == (1, 8)
endfunction


call VPTestTools_run_tests("VPClientTest")
