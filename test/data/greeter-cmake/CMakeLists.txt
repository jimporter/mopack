cmake_minimum_required(VERSION 3.0)
project(greeter)

include(mopack.cmake)
mopack_resolve()
mopack_linkage(hello)

add_library(greeter SHARED src/greeter.cpp)
target_compile_definitions(greeter PRIVATE LIBGREETER_EXPORTS)
target_include_directories(greeter PUBLIC include)
set_target_properties(greeter PROPERTIES PUBLIC_HEADER include/greeter.hpp)
target_link_libraries(greeter PUBLIC PkgConfig::hello)

install(TARGETS greeter
        LIBRARY DESTINATION lib
        PUBLIC_HEADER DESTINATION include)
