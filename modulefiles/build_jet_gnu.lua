help([[
This module calls an external shell script and sets up the environment.
]])

whatis([===[Runs a shell script and loads environment variables for the MPAS Workflow]===])

load("gnu/9.2.0")
load("cmake/3.28.1")
load("openmpi/4.1.6")

setenv("PNETCDF", "/apps/pnetcdf/1.11.2/gnu/gcc-9.2.0/")
setenv("CMAKE_C_COMPILER", "gcc")
setenv("CMAKE_CXX_COMPILER", "g++")
setenv("CMAKE_Fortran_COMPILER", "gfortran")
