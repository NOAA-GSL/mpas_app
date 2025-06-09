#!/bin/bash -e

#usage instructions
usage () {
cat << EOF_USAGE
Usage: $0 --platform=PLATFORM [OPTIONS] 

OPTIONS
  -h, --help
      show this help guide
  -p, --platform=PLATFORM
      name of machine you are building on
      (e.g. hera | jet | hercules | ursa)
  -c, --compiler=COMPILER
      compiler to use; default depends on platform
      (e.g. intel | gnu | gcc)
  --continue
      continue with existing build
  --clean
      does a "make clean"
  --exec-dir=EXEC_DIR
      installation binary directory name ("exec" by default; any name is available)
  --conda-dir=CONDA_DIR
      installation location for miniconda (SRW clone conda subdirectory by default)
  --build-jobs=BUILD_JOBS
      number of build jobs; defaults to 4
  -v, --verbose
      build with verbose output
  --atmos-only
      build the MPAS atmosphere core only, this option assumes you have already built the init_atmosphere_model to create the necessary initial conditions and executables.
  --debug
      build MPAS with debug mode
  --use-papi
      builds version of MPAS using PAPI for timers
  --tau
      builds version of MPAS using TAU hooks for profiling
  --autoclean
      forces a clean of MPAS infrastructure prior to build new core
  --gen-f90
      generates intermediate .f90 files through CPP, and builds with them
  --timer-lib=TIMER_LIB
      selects the timer library interface to be used for profiling the model, options are native, gptl, and tau
  --openmp
      builds and links with OpenMP flags
  --single-precision
      builds with default single-precision real kind.  Default is to use double-precision
EOF_USAGE
}

install_miniforge () {

  local hardware installer os version
  set -x
  os=$(uname)
  test $os == Darwin && os=MacOSX
  hardware=$(uname -m)
  installer=Miniforge3-$os-$hardware.sh
  version=25.3.0-3
  curl -L -O https://github.com/conda-forge/miniforge/releases/download/$version/$installer
  bash $installer -bfp $CONDA_DIR
  rm -v $installer
  cat <<EOF >$CONDA_DIR/.condarc
notify_outdated_conda: false
EOF
}

install_conda_envs () {

  source $CONDA_DIR/etc/profile.d/conda.sh
  conda activate
  if ! conda env list | grep -q "^mpas_app\s" ; then
    conda env create -y -n mpas_app --file environment.yml
  fi
  APPLICATION=$(echo ${APPLICATION} | tr '[a-z]' '[A-Z]')
  if ! conda env list | grep -q "^ungrib\s" ; then
    conda create -y -n ungrib -c maddenp ungrib
  fi
}

install_mpas_init () {

  pushd ${MPAS_APP_DIR}/src/MPAS-Model
  make clean CORE=atmosphere
  make clean CORE=init_atmosphere
  if [[ ${COMPILER} = "gnu" ]]; then
    build_target="gfortran"
  fi
  make ${build_target:-intel-mpi} CORE=init_atmosphere ${MPAS_MAKE_OPTIONS}
  cp -v init_atmosphere_model ${EXEC_DIR}
  make clean CORE=init_atmosphere
  popd
}

install_mpas_model () {

  pushd ${MPAS_APP_DIR}/src/MPAS-Model
  make clean CORE=atmosphere
  if [[ ${COMPILER} = "gnu" ]]; then
    build_target="gfortran"
  fi
  make ${build_target:-intel-mpi} CORE=atmosphere ${MPAS_MAKE_OPTIONS}
  cp -v atmosphere_model ${EXEC_DIR}
  ./build_tables_tempo
  popd
}

install_mpassit () {
  module purge
  pushd ${MPAS_APP_DIR}/src/MPASSIT
  compiler=intel
  if [[ $PLATFORM == ursa ]] ; then
    compiler=intel-llvm
  fi
  ./build.sh $PLATFORM $compiler
  cp -v bin/mpassit ${EXEC_DIR}
  popd
}

install_upp () {
  module purge
  module use $MPAS_APP_DIR/src/UPP/modulefiles
  module load $PLATFORM
  d=$MPAS_APP_DIR/build_upp
  mkdir -pv $d
  pushd $d
  args=(
    -DCMAKE_INSTALL_PREFIX=$MPAS_APP_DIR
    -DCMAKE_INSTALL_BINDIR="exec"
    -DBUILD_WITH_WRFIO=ON
    $MPAS_APP_DIR/src/UPP/
  )
  cmake ${args[*]} 
  make -j 8
  make install
  popd
}

# print settings
settings () {
cat << EOF_SETTINGS
Settings:

  MPAS_APP_DIR=${MPAS_APP_DIR}
  EXEC_DIR=${EXEC_DIR}
  PLATFORM=${PLATFORM}
  COMPILER=${COMPILER}
  CONTINUE=${CONTINUE}
  BUILD_JOBS=${BUILD_JOBS}
  VERBOSE=${VERBOSE}
  
EOF_SETTINGS
}

# print usage error and exit
usage_error () {
  printf "ERROR: $1\n" >&2
  usage >&2
  exit 1
}


# default settings
LCL_PID=$$
CONDA_DIR=./conda
COMPILER=""
BUILD_JOBS=4
CONTINUE=false
VERBOSE=false
ATMOS_ONLY=false
DEBUG=false
USE_PAPI=false
TAU=false
AUTOCLEAN=false
GEN_F90=false
OPENMP=false
SINGLE_PRECISION=false

# Make options
CLEAN=false


# process optional arguments
while :; do
  case $1 in
    --help|-h) usage; exit 0 ;;
    --platform=?*|-p=?*) PLATFORM=${1#*=} ;;
    --platform|--platform=|-p|-p=) usage_error "$1 requires argument." ;;
    --compiler=?*|-c=?*) COMPILER=${1#*=} ;;
    --compiler|--compiler=|-c|-c=) usage_error "$1 requires argument." ;;
    --continue) CONTINUE=true ;;
    --continue=?*|--continue=) usage_error "$1 argument ignored." ;;
    --clean) CLEAN=true ;;
    --build) BUILD=true ;;
    --exec-dir=?*) EXEC_DIR=${1#*=} ;;
    --exec-dir|--exec-dir=) usage_error "$1 requires argument." ;;
    --conda-dir=?*) CONDA_DIR=${1#*=} ;;
    --conda-dir|--conda-dir=) usage_error "$1 requires argument." ;;
    --build-jobs=?*) BUILD_JOBS=$((${1#*=})) ;;
    --build-jobs|--build-jobs=) usage_error "$1 requires argument." ;;
    --verbose|-v) VERBOSE=true ;;
    --verbose=?*|--verbose=) usage_error "$1 argument ignored." ;;
    --atmos-only ) ATMOS_ONLY=true ;;
    --debug) DEBUG=true ;;
    --use-papi) USE_PAPI=true ;;
    --tau ) TAU=true ;;
    --autoclean ) AUTOCLEAN=true ;;
    --gen-f90 ) GEN_F90=true ;;
    --timer-lib=?*) TIMER_LIB=${1#*=} ;;
    --timer-lib| --timer-lib= ) usage_error "$1 requires argument." ;;
    --openmp ) OPENMP=true ;;
    --single-precision ) SINGLE_PRECISION=true ;;
   # unknown
    -?*|?*) usage_error "Unknown option $1" ;;
    *) break
  esac
  shift
done

# Ensure uppercase / lowercase ============================================
PLATFORM=$(echo ${PLATFORM} | tr '[A-Z]' '[a-z]')
COMPILER=$(echo ${COMPILER} | tr '[A-Z]' '[a-z]')

# check if PLATFORM is set
if [ -z $PLATFORM ] ; then
  printf "\nERROR: Please set PLATFORM.\n\n"
  usage
  exit 0
fi

# set PLATFORM (MACHINE)
MACHINE="${PLATFORM}"
printf "PLATFORM(MACHINE)=${PLATFORM}\n" >&2

if [ ! -d $CONDA_DIR ]; then
  install_miniforge
  install_conda_envs
fi

# check if COMPILER is set to gcc and reset as gnu
if [ "${COMPILER}" = "gcc" ]; then
  export COMPILER="gnu"
fi

# Conda environment should have linux utilities to perform these tasks on macos.
MPAS_APP_DIR=$(cd "$(dirname "$(readlink -f -n "${BASH_SOURCE[0]}" )" )" && pwd -P)
CONDA_DIR=$(readlink -f $CONDA_DIR)
EXEC_DIR=${EXEC_DIR:-${MPAS_APP_DIR}/exec}
echo $CONDA_DIR > $MPAS_APP_DIR/conda_loc

if [ -z "${COMPILER}" ] ; then
  case ${PLATFORM} in
    jet|hera|hercules) COMPILER=intel ;;
    *)
    COMPILER=intel
printf "WARNING: Setting default COMPILER=intel for new platform ${PLATFORM}\n" >&2;
    ;;
  esac
fi

printf "COMPILER=${COMPILER}\n" >&2

# print settings
if [ "${VERBOSE}" = true ] ; then
  settings
fi

# set MODULE_FILE for this platform/compiler combination
MODULE_FILE="build_${PLATFORM}_${COMPILER}"
if [[ "$PLATFORM" == "ursa" ]] ; then
  MODULE_FILE="${MODULE_FILE}_ifort"
fi
if [ ! -f "${MPAS_APP_DIR}/modulefiles/${MODULE_FILE}.lua" ]; then
  printf "ERROR: module file does not exist for platform/compiler\n" >&2
  printf "  MODULE_FILE=${MODULE_FILE}\n" >&2
  printf "  PLATFORM=${PLATFORM}\n" >&2
  printf "  COMPILER=${COMPILER}\n\n" >&2
  printf "Please make sure PLATFORM and COMPILER are set correctly\n" >&2
  usage >&2
  exit 64
fi

printf "MODULE_FILE=${MODULE_FILE}\n" >&2

# make settings
MAKE_SETTINGS="-j ${BUILD_JOBS}"
if [ "${VERBOSE}" = true ]; then
  MAKE_SETTINGS="${MAKE_SETTINGS} VERBOSE=1"
fi

# Before we go on load modules, we first need to activate Lmod for some systems
source ${MPAS_APP_DIR}/etc/lmod-setup.sh $MACHINE

# source the module file for this platform/compiler combination, then build the code
printf "... Load MODULE_FILE ...\n"
module use ${MPAS_APP_DIR}/modulefiles
module load ${MODULE_FILE}
module list

# build MPAS
printf "...Building MPAS-Model..."

# process MPAS flags
MPAS_MAKE_OPTIONS="${MAKE_SETTINGS}"

if [ "${DEBUG}" = true ]; then
  MPAS_MAKE_OPTIONS="${MAKE_OPTIONS} DEBUG=true"
fi

if [ "${USE_PAPI}" = true ]; then
  MPAS_MAKE_OPTIONS="${MAKE_OPTIONS} USE_PAPI=true"
fi

if [ "${TAU}" = true ]; then
  MPAS_MAKE_OPTIONS="${MAKE_OPTIONS} TAU=true"
fi

if [ "${AUTOCLEAN}" = true ]; then
  MPAS_MAKE_OPTIONS="${MAKE_OPTIONS} AUTOCLEAN=true"
fi

if [ "${GEN_F90}" = true ]; then
  MPAS_MAKE_OPTIONS="${MAKE_OPTIONS} GEN_F90=true"
fi

if [ ! -z "${TIMER_LIB}" ]; then
  MPAS_MAKE_OPTIONS="${MAKE_OPTIONS} TIMER_LIB={$TIMER_LIB}"
fi

if [ "${OPENMP}" = true ]; then
  MPAS_MAKE_OPTIONS="${MAKE_OPTIONS} OPENMP=true"
fi

if [ "${SINGLE_PRECISION}" = true ]; then
  MPAS_MAKE_OPTIONS="${MAKE_OPTIONS} PRECISION=single"
fi

EXEC_DIR="${MPAS_APP_DIR}/exec"
if [ ! -d "$EXEC_DIR" ]; then
  mkdir "$EXEC_DIR"
fi

printf "\nATMOS_ONLY: ${ATMOS_ONLY}\n"

if [ ${ATMOS_ONLY} = false ]; then
  install_mpas_init
fi

install_mpas_model
install_mpassit
if [[ $PLATFORM != ursa ]] ; then
  install_upp
fi

if [ "${CLEAN}" = true ]; then
    if [ -f $PWD/Makefile ]; then
       printf "... Clean executables ...\n"
       make ${MAKE_SETTINGS} clean 2>&1 | tee log.make
    fi
fi
