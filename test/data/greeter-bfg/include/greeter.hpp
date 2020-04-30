#ifndef INC_GREETER_HPP
#define INC_GREETER_HPP

#if defined(_WIN32) && !defined(LIBGREETER_STATIC)
#  ifdef LIBGREETER_EXPORTS
#    define LIBGREETER_PUBLIC __declspec(dllexport)
#  else
#    define LIBGREETER_PUBLIC __declspec(dllimport)
#  endif
#else
#  define LIBGREETER_PUBLIC
#endif

namespace greeter {
  void LIBGREETER_PUBLIC greet();
}

#endif
