help([[
This module calls an external shell script and sets up the environment.
]])

--[[whatis([===[Loads libraries needed for building the MPAS App on Hera ]===])
prepend_path("MODULEPATH", "/scratch1/NCEPDEV/nems/role.epic/spack-stack/spack-stack-1.5.1/envs/unified-env-rocky8/install/modulefiles/Core")

load("stack-gcc/9.2.0")]]

load("cmake/3.28.1")
load("gnu")
load("openmpi/4.1.6")

setenv("PNETCDF", "/apps/pnetcdf/1.11.2/gnu/gcc-9.2.0/")
setenv("CMAKE_C_COMPILER", "gcc")
setenv("CMAKE_CXX_COMPILER", "g++")
setenv("CMAKE_Fortran_COMPILER", "gfortran")
