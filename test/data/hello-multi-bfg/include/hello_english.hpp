#ifndef INC_HELLO_ENGLISH_HPP
#define INC_HELLO_ENGLISH_HPP

#if defined(_WIN32) && !defined(LIBHELLO_ENGLISH_STATIC)
#  ifdef LIBHELLO_ENGLISH_EXPORTS
#    define LIBHELLO_ENGLISH_PUBLIC __declspec(dllexport)
#  else
#    define LIBHELLO_ENGLISH_PUBLIC __declspec(dllimport)
#  endif
#else
#  define LIBHELLO_ENGLISH_PUBLIC
#endif

namespace hello {
  namespace english {
    void LIBHELLO_ENGLISH_PUBLIC say_hello();
  }
}

#endif
