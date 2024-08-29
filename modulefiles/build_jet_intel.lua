help([[
This module loads libraries for building the MPAS App on
the NOAA RDHPC machine Jet using Intel-2021.5.0
]])

whatis([===[Loads libraries needed for building the MPAS Workflow on Jet ]===])
prepend_path("MODULEPATH","/mnt/contrib/spack-stack/spack-stack-1.6.0/envs/unified-env-rocky8/install")

load("intel/2021.5.0")
load("cmake/3.28.1")
load("gnu")
load("intel/2023.2.0")
load("impi/2023.2.0")

load("pnetcdf/1.12.3")
load("szip")
load("hdf5parallel/1.10.5")
load("netcdf-hdf5parallel/4.7.0")

setenv("CMAKE_C_COMPILER","mpiicc")
setenv("CMAKE_CXX_COMPILER", "mpiicc")
setenv("CMAKE_Fortran_COMPILER", "mpiifort")
