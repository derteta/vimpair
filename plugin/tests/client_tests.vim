execute("source " . expand("<sfile>:p:h") . "/test_tools.vim")
execute("source " . expand("<sfile>:p:h") . "/../vimpair.vim")

call g:VimpairRunPython("from mock import Mock")

let g:VimpairShowStatusMessages = 0
let g:VimpairTimerInterval = 1

function! _VPClientTest_set_up()
  execute("vnew")
  let g:VPClientTest_SentMessages = []
  call g:VimpairRunPython(
        \ "fake_socket = Mock(sendall=lambda b: vim.command(" .
        \ "    'call add(g:VPClientTest_SentMessages, \"%s\")' % str(b)))"
        \)
  call g:VimpairRunPython("client_socket_factory = lambda: fake_socket")
  VimpairClientStart
endfunction

function! _VPClientTest_tear_down()
  VimpairClientStop
  unlet g:VPClientTest_SentMessages
  execute("q!")
endfunction

function! s:VPClientTest_set_received_messages(messages)
  let g:VPClientTest_ReceivedMessages = a:messages
  call g:VimpairRunPython(
        \ "received_messages = list(vim.eval('g:VPClientTest_ReceivedMessages'))")
  call g:VimpairRunPython("fake_socket.recv = lambda *a: received_messages.pop()")
  unlet g:VPClientTest_ReceivedMessages
endfunction

function! s:VPClientTest_take_control()
  call s:VPClientTest_set_received_messages(["VIMPAIR_TAKE_CONTROL"])
  call s:VPClientTest_wait_for_timer()
endfunction

function! s:VPClientTest_assert_buffer_has_contents(expected)
  let l:actual = getline(1, '$')
  call assert_equal(a:expected, l:actual)
endfunction

function! s:VPClientTest_assert_has_sent_message(expected)
  for message in g:VPClientTest_SentMessages
    if message == a:expected
      return
    endif
  endfor
  call assert_report("Expected message has not been sent: " . a:expected)
endfunction

function! s:VPClientTest_wait_for_timer()
  sleep 3m
endfunction


function! VPClientTest_applies_received_contents_updates()
  call s:VPClientTest_set_received_messages(["VIMPAIR_FULL_UPDATE|16|This is line one"])

  call s:VPClientTest_wait_for_timer()

  call s:VPClientTest_assert_buffer_has_contents(["This is line one"])
endfunction

function! VPClientTest_received_contents_updates_overwrite_existing_contents()
  execute("normal i1")
  execute("normal o2")
  call s:VPClientTest_set_received_messages(["VIMPAIR_FULL_UPDATE|16|This is line one"])

  call s:VPClientTest_wait_for_timer()

  call s:VPClientTest_assert_buffer_has_contents(["This is line one"])
endfunction

function! VPClientTest_received_cursor_position_is_applied()
  execute("normal iThis is line one")
  execute("normal oThis is line two")
  call s:VPClientTest_set_received_messages(["VIMPAIR_CURSOR_POSITION|0|8"])

  call s:VPClientTest_wait_for_timer()

  let l:actual = getpos(".")[1:2]
  call assert_equal([1, 9], l:actual)
endfunction

function! VPClientTest_received_cursor_position_is_retained_after_full_update()
  execute("normal iOne")
  execute("normal oTwo")
  execute("normal oThree")
  call s:VPClientTest_set_received_messages(["VIMPAIR_CURSOR_POSITION|2|3"])
  call s:VPClientTest_wait_for_timer()

  call s:VPClientTest_set_received_messages(["VIMPAIR_FULL_UPDATE|18|One\nTwo\nThree\nFour"])
  call s:VPClientTest_wait_for_timer()

  let l:actual = getpos(".")[1:2]
  call assert_equal([3, 4], l:actual)
endfunction

function! VPClientTest_applies_large_contents_received_in_multiple_messages()
  call s:VPClientTest_set_received_messages([
        \  "VIMPAIR_CONTENTS_END|25|5678901234567890123456789",
        \  "VIMPAIR_CONTENTS_PART|998|789012345678901234567890123456789012345678901" .
        \  "234567890123456789012345678901234567890123456789012345678901234567890" .
        \  "123456789012345678901234567890123456789012345678901234567890123456789" .
        \  "012345678901234567890123456789012345678901234567890123456789012345678" .
        \  "901234567890123456789012345678901234567890123456789012345678901234567" .
        \  "890123456789012345678901234567890123456789012345678901234567890123456" .
        \  "789012345678901234567890123456789012345678901234567890123456789012345" .
        \  "678901234567890123456789012345678901234567890123456789012345678901234" .
        \  "567890123456789012345678901234567890123456789012345678901234567890123" .
        \  "456789012345678901234567890123456789012345678901234567890123456789012" .
        \  "345678901234567890123456789012345678901234567890123456789012345678901" .
        \  "234567890123456789012345678901234567890123456789012345678901234567890" .
        \  "123456789012345678901234567890123456789012345678901234567890123456789" .
        \  "012345678901234567890123456789012345678901234567890123456789012345678" .
        \  "90123456789012345678901234567890123456789012345678901234",
        \  "VIMPAIR_CONTENTS_START|997|01234567890123456789012345678901234567890123" .
        \  "456789012345678901234567890123456789012345678901234567890123456789012" .
        \  "345678901234567890123456789012345678901234567890123456789012345678901" .
        \  "234567890123456789012345678901234567890123456789012345678901234567890" .
        \  "123456789012345678901234567890123456789012345678901234567890123456789" .
        \  "012345678901234567890123456789012345678901234567890123456789012345678" .
        \  "901234567890123456789012345678901234567890123456789012345678901234567" .
        \  "890123456789012345678901234567890123456789012345678901234567890123456" .
        \  "789012345678901234567890123456789012345678901234567890123456789012345" .
        \  "678901234567890123456789012345678901234567890123456789012345678901234" .
        \  "567890123456789012345678901234567890123456789012345678901234567890123" .
        \  "456789012345678901234567890123456789012345678901234567890123456789012" .
        \  "345678901234567890123456789012345678901234567890123456789012345678901" .
        \  "234567890123456789012345678901234567890123456789012345678901234567890" .
        \  "12345678901234567890123456789012345678901234567890123456",
        \])

  call s:VPClientTest_wait_for_timer()

  call s:VPClientTest_assert_buffer_has_contents([
        \  "01234567890123456789012345678901234567890123456789012345678901234567" .
        \  "89012345678901234567890123456789012345678901234567890123456789012345" .
        \  "67890123456789012345678901234567890123456789012345678901234567890123" .
        \  "45678901234567890123456789012345678901234567890123456789012345678901" .
        \  "23456789012345678901234567890123456789012345678901234567890123456789" .
        \  "01234567890123456789012345678901234567890123456789012345678901234567" .
        \  "89012345678901234567890123456789012345678901234567890123456789012345" .
        \  "67890123456789012345678901234567890123456789012345678901234567890123" .
        \  "45678901234567890123456789012345678901234567890123456789012345678901" .
        \  "23456789012345678901234567890123456789012345678901234567890123456789" .
        \  "01234567890123456789012345678901234567890123456789012345678901234567" .
        \  "89012345678901234567890123456789012345678901234567890123456789012345" .
        \  "67890123456789012345678901234567890123456789012345678901234567890123" .
        \  "45678901234567890123456789012345678901234567890123456789012345678901" .
        \  "23456789012345678901234567890123456789012345678901234567890123456789" .
        \  "01234567890123456789012345678901234567890123456789012345678901234567" .
        \  "89012345678901234567890123456789012345678901234567890123456789012345" .
        \  "67890123456789012345678901234567890123456789012345678901234567890123" .
        \  "45678901234567890123456789012345678901234567890123456789012345678901" .
        \  "23456789012345678901234567890123456789012345678901234567890123456789" .
        \  "01234567890123456789012345678901234567890123456789012345678901234567" .
        \  "89012345678901234567890123456789012345678901234567890123456789012345" .
        \  "67890123456789012345678901234567890123456789012345678901234567890123" .
        \  "45678901234567890123456789012345678901234567890123456789012345678901" .
        \  "23456789012345678901234567890123456789012345678901234567890123456789" .
        \  "01234567890123456789012345678901234567890123456789012345678901234567" .
        \  "89012345678901234567890123456789012345678901234567890123456789012345" .
        \  "67890123456789012345678901234567890123456789012345678901234567890123" .
        \  "45678901234567890123456789012345678901234567890123456789012345678901" .
        \  "234567890123456789012345678901234567890123456789"])
endfunction

function! VPClientTest_send_buffer_contents_after_taking_control()
  call s:VPClientTest_take_control()

  execute("normal iThis is just some text")

  call s:VPClientTest_assert_has_sent_message(
    \ "VIMPAIR_FULL_UPDATE|22|This is just some text")
endfunction

function! VPClientTest_send_cursor_position_after_taking_control()
  call s:VPClientTest_take_control()

  execute("normal iThis is line one")
  execute("normal oThis is line two")

  execute("normal gg0ww")
  " The CursorMoved autocommand is not reported in this scope,
  " so we need to manually trigger it
  execute("doautocmd CursorMoved")

  call s:VPClientTest_assert_has_sent_message("VIMPAIR_CURSOR_POSITION|0|8")
endfunction

function! VPClientTest_doesnt_apply_received_contents_updates_after_taking_control()
  call s:VPClientTest_take_control()

  call s:VPClientTest_set_received_messages(["VIMPAIR_FULL_UPDATE|16|This is line one"])
  call s:VPClientTest_wait_for_timer()

  call s:VPClientTest_assert_buffer_has_contents([""])
endfunction

function! VPClientTest_creates_new_buffer_with_filename_on_receiving_file_changed_message()
  call s:VPClientTest_set_received_messages(["VIMPAIR_FILE_CHANGE|11|SomeFile.py"])

  call s:VPClientTest_wait_for_timer()

  " On Mac, we set up the session folder in /var/folders/..., but vim reports
  " the buffer path as /private/var/folders/..., which is synonymous
  call g:VimpairRunPython(
        \  "vim.command(" .
        \  "   'let g:VPServerTests_expected = \"%s\"'" .
        \  "   % session.prepend_folder('SomeFile.py')" .
        \  ")"
        \)
  call assert_match(".*" . g:VPServerTests_expected, expand("%"))
  unlet g:VPServerTests_expected
endfunction

function! VPClientTest_doesnt_send_file_change_on_change_after_taking_control()
  call s:VPClientTest_take_control()

  execute("silent e " . expand("%:p:h") . "/../README.md")

  call assert_equal([], g:VPClientTest_SentMessages)
endfunction

function! VPClientTest_saves_current_file_when_receiving_save_message()
  call s:VPClientTest_set_received_messages(["VIMPAIR_FILE_CHANGE|18|Folder/SomeFile.py"])
  call s:VPClientTest_wait_for_timer()

  call s:VPClientTest_set_received_messages(["VIMPAIR_SAVE_FILE"])
  call s:VPClientTest_wait_for_timer()

  " Regression test: saving a second time would raise an error
  call s:VPClientTest_set_received_messages(["VIMPAIR_SAVE_FILE"])
  call s:VPClientTest_wait_for_timer()

  call g:VimpairRunPython(
        \  "vim.command(" .
        \  "   'let g:VPServerTests_expected = \"%s\"'" .
        \  "   % session.prepend_folder('Folder/SomeFile.py')" .
        \  ")"
        \)
  call assert_false(empty(glob(g:VPServerTests_expected)))
  unlet g:VPServerTests_expected
endfunction


call VPTestTools_run_tests("VPClientTest")
