help([[
This module loads libraries for building the MPAS App on
the NOAA RDHPC machine Hera using Intel-2022.1.2
]])

whatis([===[Loads libraries needed for building the MPAS App on Hera ]===])

load("cmake/3.23.1")
load("gnu")
load("intel/2022.1.2")
load("impi/2022.1.2")

load("pnetcdf/1.11.2")
load("szip")
load("hdf5parallel/1.10.6")
load("netcdf-hdf5parallel/4.7.0")

setenv("PNETCDF", "/apps/pnetcdf/1.11.2/intel/2022.1.2")
setenv("CMAKE_C_COMPILER", "mpiicc")
setenv("CMAKE_CXX_COMPILER", "mpiicpc")
setenv("CMAKE_Fortran_COMPILER", "mpiifort")

