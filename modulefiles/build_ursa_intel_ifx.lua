help([[
This module loads libraries for building the MPAS App on
the NOAA RDHPC machine Ursa using Intel-2024.2.1
]])

--[[whatis([===[Loads libraries needed for building the MPAS App on Ursa ]===])]]

load("cmake/3.30.2")
load("intel-oneapi-compilers/2024.2.1")
load("intel-oneapi-mpi/2021.13.1")
load("parallel-netcdf/1.12.3")

--[[ This path comes from the module's PARALLEL_NETCDF_ROOT env variable]]
setenv("PNETCDF", "/apps/spack-2024-12/linux-rocky9-x86_64/oneapi-2024.2.1/parallel-netcdf-1.12.3-xynwqn25sqarwdvdmsoejsryxdyj73x4/")

setenv("CMAKE_C_COMPILER", "mpiicc")
setenv("CMAKE_CXX_COMPILER", "mpiicpc")
setenv("CMAKE_Fortran_COMPILER", "mpiifort")

