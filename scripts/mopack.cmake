cmake_minimum_required(VERSION 3.0...4.0)

find_package(PkgConfig REQUIRED)

macro(_to_unix_path VAR)
  string(REPLACE ";" ":" ${VAR} "${${VAR}}")
endmacro()

macro(_to_windows_path VAR)
  string(REPLACE ":" ";" ${VAR} "${${VAR}}")
endmacro()

macro(_get_path KIND OUTVAR)
  string(TOUPPER ${KIND} _get_path_kindupper)
  list(TRANSFORM CMAKE_SYSTEM_PREFIX_PATH APPEND "/${KIND}"
    OUTPUT_VARIABLE ${OUTVAR})
  # Remove any double-slashes from our list; `CMAKE_SYSTEM_PREFIX_PATH` can
  # include just "/" as a directory.
  string(REPLACE "//" "/" ${OUTVAR} "${${OUTVAR}}")

  list(APPEND ${OUTVAR} ${CMAKE_SYSTEM_${_get_path_kindupper}_PATH})
  list(PREPEND ${OUTVAR} ${CMAKE_${_get_path_kindupper}_PATH})

  set(_get_path_env $ENV{CMAKE_${_get_path_kindupper}_PATH})
  _to_windows_path(_get_path_env)
  list(PREPEND ${OUTVAR} ${_get_path_env})
endmacro()

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
  # First, set up environment variables for mopack.

  # MOPACK_INCLUDE_PATH
  _get_path(include include_path)
  if(NOT WINDOWS)
    _to_unix_path(include_path)
  endif()
  set(ENV{MOPACK_INCLUDE_PATH} "${include_path}")

  # MOPACK_LIB_PATH
  _get_path(lib lib_path)
  if(NOT WINDOWS)
    _to_unix_path(lib_path)
  endif()
  set(ENV{MOPACK_LIB_PATH} "${lib_path}")

  # MOPACK_LIB_NAMES
  set(lib_names "\
${CMAKE_STATIC_LIBRARY_PREFIX}{}${CMAKE_STATIC_LIBRARY_SUFFIX};\
${CMAKE_SHARED_LIBRARY_PREFIX}{}${CMAKE_SHARED_LIBRARY_SUFFIX}")
  if(NOT WINDOWS)
    _to_unix_path(lib_names)
  endif()
  set(ENV{MOPACK_LIB_NAMES} ${lib_names})

  # MOPACK_AUTO_LINE
  if(MSVC)
    set(ENV{MOPACK_AUTO_LINK} "true")
  endif()

  # Finally, call `mopack resolve`.
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
    _to_windows_path(pkgconf_path)
  endif()

  set(ENV{PKG_CONFIG_PATH} "${pkgconf_path}")
  pkg_check_modules(
    ${package}
    REQUIRED IMPORTED_TARGET
    ${pkgconf_pcnames}
  )
endfunction()
