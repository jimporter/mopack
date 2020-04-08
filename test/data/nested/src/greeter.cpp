#include "greeter.hpp"
#include "hello.hpp"

#include <iostream>

namespace greeter {
  void LIBGREETER_PUBLIC greet() {
    hello::say_hello();
  }
}
