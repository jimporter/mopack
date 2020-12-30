cmake_minimum_required(VERSION 3.0)

find_package(PkgConfig REQUIRED)

macro(_jq FILE)
  cmake_parse_arguments(JQ_ARGS "" "OUT" "QUERY" ${ARGN})
  execute_process(
    COMMAND jq -r ${JQ_ARGS_QUERY}
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

function(mopack_usage package)
  set(usage_file "${CMAKE_BINARY_DIR}/.cmake_mopack_usage")
  execute_process(
    COMMAND mopack usage ${package} --json --directory ${CMAKE_BINARY_DIR}
    OUTPUT_FILE ${usage_file}
  )

  _jq(${usage_file} QUERY .path OUT pkgconf_path)
  _jq(${usage_file} QUERY .pcfiles[] OUT pkgconf_pcfiles)
  string(REPLACE "\n" " " pkgconf_pcfiles "${pkgconf_pcfiles}")

  set(ENV{PKG_CONFIG_PATH} ${pkgconf_path})
  pkg_check_modules(
    ${package}
    REQUIRED IMPORTED_TARGET
    ${pkgconf_pcfiles}
  )
endfunction()