cmake_minimum_required(VERSION 3.17)
project(hello)

add_library(hello SHARED src/hello.cpp)
target_compile_definitions(hello PRIVATE LIBHELLO_EXPORTS)
target_include_directories(hello PUBLIC include)
set_target_properties(hello PROPERTIES PUBLIC_HEADER include/hello.hpp)

install(TARGETS hello
        LIBRARY DESTINATION lib
        PUBLIC_HEADER DESTINATION include)
