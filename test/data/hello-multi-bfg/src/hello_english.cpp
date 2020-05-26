#include "hello_english.hpp"

#include <iostream>

namespace hello {
  namespace english {
    void LIBHELLO_ENGLISH_PUBLIC say_hello() {
      std::cout << "hello, world!" << std::endl;
    }
  }
}
