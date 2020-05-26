#include "hello_french.hpp"

#include <iostream>

namespace hello {
  namespace french {
    void LIBHELLO_FRENCH_PUBLIC say_hello() {
      std::cout << "bonjour, monde!" << std::endl;
    }
  }
}
