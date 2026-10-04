cmake_minimum_required(VERSION 3.0...4.0)

find_package(PkgConfig REQUIRED)

function(_checked_execute_error COMMAND STATUS STDERR)
  set(errmsg "${COMMAND} failed with status ${STATUS}")
    if(NOT STDERR STREQUAL "")
      string(APPEND errmsg ":\n" ${STDERR})
    endif()
    message(FATAL_ERROR ${errmsg})
endfunction()

macro(_checked_execute_process)
  execute_process(
    ERROR_VARIABLE _chexec_stderr
    RESULT_VARIABLE _chexec_status
    ${ARGN}
  )
  if(NOT ${_chexec_status} EQUAL 0)
    cmake_parse_arguments(_CHEXEC_ARGS "" "" "COMMAND" ${ARGN})
    list(GET _CHEXEC_ARGS_COMMAND 0 _chexec_cmd)
    _checked_execute_error(${_chexec_cmd} "${_chexec_status}"
      "${_chexec_stderr}")
  endif()
endmacro()

macro(_jq FILE)
  cmake_parse_arguments(_JQ_ARGS "" "OUT;QUERY" "" ${ARGN})
  _checked_execute_process(
    COMMAND jq -r "${_JQ_ARGS_QUERY}"
    INPUT_FILE ${FILE}
    OUTPUT_VARIABLE ${_JQ_ARGS_OUT}
    OUTPUT_STRIP_TRAILING_WHITESPACE
  )
endmacro()

function(mopack_resolve)
  execute_process(
    COMMAND mopack resolve ${CMAKE_SOURCE_DIR} --directory ${CMAKE_BINARY_DIR}
    ERROR_VARIABLE stderr
    RESULT_VARIABLE exit_status
  )
  if(NOT ${exit_status} EQUAL 0 AND NOT ${exit_status} EQUAL 3)
    _checked_execute_error("mopack" "${exit_status}" "${stderr}")
  endif()
endfunction()

function(mopack_linkage package)
  set(linkage_file "${CMAKE_BINARY_DIR}/.cmake_mopack_linkage")
  _checked_execute_process(
    COMMAND mopack linkage ${package} --json --directory ${CMAKE_BINARY_DIR}
    OUTPUT_FILE ${linkage_file}
  )

  _jq(${linkage_file} QUERY ".pkg_config_path | join(\":\")" OUT pkgconf_path)
  _jq(${linkage_file} QUERY ".pcnames | join(\" \")" OUT pkgconf_pcnames)

  if(WINDOWS)
    string(REPLACE ":" ";" pkgconf_path "${pkgconf_path}")
  endif()

  set(ENV{PKG_CONFIG_PATH} "${pkgconf_path}")
  pkg_check_modules(
    ${package}
    REQUIRED IMPORTED_TARGET
    ${pkgconf_pcnames}
  )
endfunction()
