help([[
This module loads libraries for building the MPAS App on
the NOAA RDHPC machine Hera using Intel-2023.2.0
]])

whatis([===[Loads libraries needed for building the MPAS App on Hera ]===])

load("cmake/3.28.1")
load("gnu")
load("intel/2023.2.0")
load("impi/2023.2.0")

--prepend_path("PATH", "/apps/oneapi/mpi/2021.10.0/bin")
--prepend_path("LD_LIBRARY_PATH", "/apps/oneapi/mpi/2021.10.0/lib")

load("pnetcdf/1.12.3")
load("szip")
load("hdf5parallel/1.10.5")
load("netcdf-hdf5parallel/4.7.0")

setenv("PNETCDF", "/apps/pnetcdf/1.12.3/intel_2023.2.0-impi")
setenv("CMAKE_C_COMPILER", "mpiicc")
setenv("CMAKE_CXX_COMPILER", "mpiicpc")
setenv("CMAKE_Fortran_COMPILER", "mpiifort")

