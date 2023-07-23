cmake_minimum_required(VERSION 3.0)

find_package(PkgConfig REQUIRED)

macro(_jq FILE)
  cmake_parse_arguments(JQ_ARGS "" "OUT" "QUERY" ${ARGN})
  execute_process(
    COMMAND jq -r "${JQ_ARGS_QUERY}"
    INPUT_FILE ${FILE}
    OUTPUT_VARIABLE ${JQ_ARGS_OUT}
    OUTPUT_STRIP_TRAILING_WHITESPACE
  )
endmacro()

function(mopack_resolve)
  execute_process(
    COMMAND mopack resolve ${CMAKE_SOURCE_DIR} --directory ${CMAKE_BINARY_DIR}
  )
endfunction()

function(mopack_linkage package)
  set(linkage_file "${CMAKE_BINARY_DIR}/.cmake_mopack_linkage")
  execute_process(
    COMMAND mopack linkage ${package} --json --directory ${CMAKE_BINARY_DIR}
    OUTPUT_FILE ${linkage_file}
  )

  _jq(${linkage_file} QUERY ".pkg_config_path | join(\";\")" OUT pkgconf_path)
  _jq(${linkage_file} QUERY ".pcnames | join(\" \")" OUT pkgconf_pcnames)

  if(UNIX)
    string(REPLACE ";" ":" pkgconf_path "${pkgconf_path}")
  endif()

  set(ENV{PKG_CONFIG_PATH} "${pkgconf_path}")
  pkg_check_modules(
    ${package}
    REQUIRED IMPORTED_TARGET
    ${pkgconf_pcnames}
  )
endfunction()
