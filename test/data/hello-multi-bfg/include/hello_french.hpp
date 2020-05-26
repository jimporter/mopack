#ifndef INC_HELLO_FRENCH_HPP
#define INC_HELLO_FRENCH_HPP

#if defined(_WIN32) && !defined(LIBHELLO_FRENCH_STATIC)
#  ifdef LIBHELLO_FRENCH_EXPORTS
#    define LIBHELLO_FRENCH_PUBLIC __declspec(dllexport)
#  else
#    define LIBHELLO_FRENCH_PUBLIC __declspec(dllimport)
#  endif
#else
#  define LIBHELLO_FRENCH_PUBLIC
#endif

namespace hello {
  namespace french {
    void LIBHELLO_FRENCH_PUBLIC say_hello();
  }
}

#endif
