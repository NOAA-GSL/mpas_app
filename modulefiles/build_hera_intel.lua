help([[
This module loads libraries for building the MPAS App on
the NOAA RDHPC machine Hera using Intel-2022.1.2
]])

whatis([===[Loads libraries needed for building the MPAS App on Hera ]===])

prepend_path("MODULEPATH", "/scratch1/NCEPDEV/nems/role.epic/spack-stack/spack-stack-1.5.1/envs/unified-env-rocky8/install/modulefiles/Core")


load("stack-intel/2021.5.0")
load("stack-intel-oneapi-mpi")
load("cmake/3.23.1")
load("intel/2022.1.2")
load("impi/2022.1.2")

load("pnetcdf")
load("szip")
load("hdf5parallel/1.10.6")
load("netcdf-hdf5parallel/4.7.4")

setenv("PNETCDF", "/apps/pnetcdf/1.11.2/intel/2022.1.2")
setenv("CMAKE_C_COMPILER", "mpiicc")
setenv("CMAKE_CXX_COMPILER", "mpiicpc")
setenv("CMAKE_Fortran_COMPILER", "mpiifort")

