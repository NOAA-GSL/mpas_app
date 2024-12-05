help([[
This module calls an external shell script and sets up the environment.
]])
whatis([===[Runs a shell script and loads environment variables for the MPAS Workflow]===])

load("gcc/12.2.0")
load("cmake/3.26.3")
load("openmpi/4.1.4")

setenv("PNETCDF", "/apps/spack-managed/gcc-12.2.0/parallel-netcdf-1.12.2-6i23ebgbsjylqskl3a25idthon3sijx4")
setenv("CMAKE_C_COMPILER", "gcc")
setenv("CMAKE_CXX_COMPILER", "g++")
setenv("CMAKE_Fortran_COMPILER", "gfortran")
