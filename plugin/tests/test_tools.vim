" To use these functions, the calling script needs to name its functions
" using a common prefix (referred to as 'namespace').
" Tests need to be name '<namespace>_<test_case_name>'.
" The script is also required to provide '_<namespace>_set_up' and
" '_<namespace>_tear_down (the leading '_' allows distinction from the tests).

" To filter tests by name, set g:VPTestTools_name_filter accordingly. Only the
" tests whose names match this filter string will be run.


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
    let l:test_name = s:VPTestTools_funcref_string_to_name(Test)
    if !exists("g:VPTestTools_name_filter")
      \ || match(l:test_name, g:VPTestTools_name_filter) >= 0
      let result += [l:test_name]
    endif
  endfor
  return l:result
endfunction


function! s:VPTestTools_show_errors()
  for error in v:errors
     :echoerr error
  endfor
  let v:errors = []
endfunction


function! VPTestTools_run_tests(namespace)
  let Set_up = function("_" . a:namespace . "_set_up")
  let Tear_down = function("_" . a:namespace . "_tear_down")

  for Test in s:VPTestTools_get_tests(a:namespace)
    echo "Running ".Test
    call l:Set_up()
    call function(Test)()
    call l:Tear_down()
    call s:VPTestTools_show_errors()
  endfor
endfunction
