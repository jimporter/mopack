#include "hello.hpp"

#include <iostream>

namespace hello {
  void LIBHELLO_PUBLIC say_hello() {
    std::cout << "hello, library!" << std::endl;
  }
}
