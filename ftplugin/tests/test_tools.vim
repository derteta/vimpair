" To use these functions, the calling script needs to name its functions
" using a common prefix (referred to as 'namespace').
" Tests need to be name '<namespace>_<test_case_name>'.
" The script is also required to provide '_<namespace>_set_up' and
" '_<namespace>_tear_down (the leading '_' allows distinction from the tests).


function! s:VPTestTools_funcref_string_to_name(funcref_string)
  let prefix_len = 9
  let num_quotes = 2
  " Each entry has the following format: 'function <name>()',
  " but we're only interested in <name>
  return strpart(
    \ a:funcref_string,
    \ prefix_len,
    \ strlen(a:funcref_string) - prefix_len - num_quotes
    \)
endfunction


function! s:VPTestTools_get_tests(namespace)
  let result = []
  for Test in split(execute("function /^" . a:namespace), '\n')
    let result += [s:VPTestTools_funcref_string_to_name(Test)]
  endfor
  return l:result
endfunction


function! VPTestTools_run_tests(namespace)
  let Set_up = function("_" . a:namespace . "_set_up")
  let Tear_down = function("_" . a:namespace . "_tear_down")

  for Test in s:VPTestTools_get_tests(a:namespace)
    echo "Running ".Test
    call Set_up()
    call function(Test)()
    call Tear_down()
  endfor
endfunction
