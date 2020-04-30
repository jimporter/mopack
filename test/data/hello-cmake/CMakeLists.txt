add_library(hello SHARED src/hello.cpp)
target_include_directories(hello PUBLIC include)
set_target_properties(hello PROPERTIES PUBLIC_HEADER include/hello.hpp)

install(TARGETS hello
        LIBRARY DESTINATION lib
        PUBLIC_HEADER DESTINATION include)
