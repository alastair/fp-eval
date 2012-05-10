#                                               -*- Autoconf -*-
# Process this file with autoconf to produce a configure script.

AC_PREREQ(2.57)
AC_INIT(FULL-PACKAGE-NAME, VERSION, BUG-REPORT-ADDRESS)
AM_INIT_AUTOMAKE(musicretr, 1.0)

AC_CONFIG_SRCDIR([mrserver.cc])
#AC_CONFIG_HEADER([config.h])
AM_CONFIG_HEADER([config.h])

# Checks for programs.
AC_PROG_CXX
AC_PROG_CC

# Checks for libraries.
AC_CHECK_LIB(fftw3, fftw_execute,,AC_MSG_ERROR(sigproc requires fftw3))
AC_CHECK_LIB(pthread, pthread_create,,AC_MSG_ERROR(csapp requires pthread))
# Checks for header files.


# Checks for typedefs, structures, and compiler characteristics.


# Checks for library functions.


AC_CONFIG_FILES([Makefile])
AC_OUTPUT

