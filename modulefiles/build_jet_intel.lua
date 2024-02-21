help([[
This module loads libraries for building the UFS SRW App on
the NOAA RDHPC machine Jet using Intel-2021.5.0
]])

whatis([===[Loads libraries needed for building the MPAS Workflow on Jet ]===])
prepend_path("MODULEPATH","/mnt/lfs4/HFIP/hfv3gfs/role.epic/spack-stack/spack-stack-1.5.0/envs/unified-env/install/modulefiles/Core")
prepend_path("MODULEPATH", "/lfs4/HFIP/hfv3gfs/spack-stack/modulefiles")

load("cmake/3.20.1")
load("gnu")
load("intel/2022.1.2")
load("impi/2022.1.2")

load("pnetcdf")
load("szip")
load("hdf5parallel/1.10.6")
load("netcdf-hdf5parallel/4.7.4")

setenv("PIO", "/lfs4/BMC/wrfruc/jderrico/mpas/PIOV2")

setenv("CMAKE_C_COMPILER","mpiicc")
setenv("CMAKE_CXX_COMPILER", "mpiicc")
setenv("CMAKE_Fortran_COMPILER", "mpiifort")
