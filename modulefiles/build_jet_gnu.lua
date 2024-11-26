help([[
This module loads libraries for building the MPAS App on
the NOAA RDHPC machine Jet using Intel-2021.5.0
]])

whatis([===[Loads libraries needed for building the MPAS Workflow on Jet ]===])


load("cmake/3.28.1")
load("gnu/14.2.0")

setenv("CMAKE_C_COMPILER","mpiicc")
setenv("CMAKE_CXX_COMPILER", "mpiicc")
setenv("CMAKE_Fortran_COMPILER", "mpiifort")
