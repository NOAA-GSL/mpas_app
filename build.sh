#!/bin/bash

#usage instructions
usage () {
cat << EOF_USAGE
Usage: $0 --platform=PLATFORM [OPTIONS] 

OPTIONS
  -h, --help
      show this help guide
  -p, --platform=PLATFORM
      name of machine you are building on
      (e.g. cheyenne | hera | jet | orion | wcoss2)
  -c, --compiler=COMPILER
      compiler to use; default depends on platform
      (e.g. intel | gnu | cray | gccgfortran)
  --continue
      continue with existing build
  --remove
      removes existing build; overrides --continue
  --clean
      does a "make clean"
  --move
      move binaries to final location.
  --build-dir=BUILD_DIR
      build directory
  --install-dir=INSTALL_DIR
      installation prefix
  --bin-dir=BIN_DIR
      installation binary directory name ("exec" by default; any name is available)
  --conda-dir=CONDA_DIR
      installation location for miniconda (SRW clone conda subdirectory by default)
  --build-jobs=BUILD_JOBS
      number of build jobs; defaults to 4
  -v, --verbose
      build with verbose output

EOF_USAGE
}

# print settings
settings () {
cat << EOF_SETTINGS
Settings:

  MPAS_DIR=${MPAS_DIR}
  BUILD_DIR=${BUILD_DIR}
  INSTALL_DIR=${INSTALL_DIR}
  BIN_DIR=${BIN_DIR}
  PLATFORM=${PLATFORM}
  COMPILER=${COMPILER}
  REMOVE=${REMOVE}
  CONTINUE=${CONTINUE}
  BUILD_JOBS=${BUILD_JOBS}
  VERBOSE=${VERBOSE}
  BUILD_MPAS=${BUILD_MPAS}

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
BIN_DIR="exec"
CONDA_BUILD_DIR="conda"
COMPILER=""
BUILD_JOBS=4
REMOVE=false
CONTINUE=false
VERBOSE=false

# Turn off all apps to build and choose default later
DEFAULT_BUILD=true
BUILD_CONDA="on"
BUILD_MPAS="off"

# Make options
CLEAN=false
MOVE=false

# process required arguments
if [[ ("$1" == "--help") || ("$1" == "-h") ]]; then
  usage
  exit 0
fi

# process optional arguments
while :; do
  case $1 in
    --help|-h) usage; exit 0 ;;
    --platform=?*|-p=?*) PLATFORM=${1#*=} ;;
    --platform|--platform=|-p|-p=) usage_error "$1 requires argument." ;;
    --compiler=?*|-c=?*) COMPILER=${1#*=} ;;
    --compiler|--compiler=|-c|-c=) usage_error "$1 requires argument." ;;
    --remove) REMOVE=true ;;
    --remove=?*|--remove=) usage_error "$1 argument ignored." ;;
    --continue) CONTINUE=true ;;
    --continue=?*|--continue=) usage_error "$1 argument ignored." ;;
    --clean) CLEAN=true ;;
    --build) BUILD=true ;;
    --move) MOVE=true ;;
    --build-dir=?*) BUILD_DIR=${1#*=} ;;
    --build-dir|--build-dir=) usage_error "$1 requires argument." ;;
    --install-dir=?*) INSTALL_DIR=${1#*=} ;;
    --install-dir|--install-dir=) usage_error "$1 requires argument." ;;
    --bin-dir=?*) BIN_DIR=${1#*=} ;;
    --bin-dir|--bin-dir=) usage_error "$1 requires argument." ;;
    --conda-dir=?*) CONDA_BUILD_DIR=${1#*=} ;;
    --conda-dir|--conda-dir=) usage_error "$1 requires argument." ;;
    --build-jobs=?*) BUILD_JOBS=$((${1#*=})) ;;
    --build-jobs|--build-jobs=) usage_error "$1 requires argument." ;;
    --verbose|-v) VERBOSE=true ;;
    --verbose=?*|--verbose=) usage_error "$1 argument ignored." ;;
    
   # unknown
    -?*|?*) usage_error "Unknown option $1" ;;
    *) break
  esac
  shift
done

# Ensure uppercase / lowercase ============================================
APPLICATION=$(echo ${APPLICATION} | tr '[a-z]' '[A-Z]')
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

if [ ! -d "$CONDA_BUILD_DIR}" ]; then
  os=$(uname)
  test $os == Darwin && os=MacOSX
  hardware=$(uname -m)
  installer=Miniforge3-${os}-${hardware}.sh
  curl -L -O "https://github.com/conda-forge/miniforge/releases/download/23.3.1-1/${installer}"
  bash ./${installer} -bfp "${CONDA_BUILD_DIR}"
  rm ${installer}
fi

source ${CONDA_BUILD_DIR}/etc/profile.d/conda.sh

conda activate
if ! conda env list | grep -q "^mpas_workflow\s" ; then
  mamba env create -n mpas_workflow --file environment.yml
fi

# Conda environment should have linux utilities to perform these tasks on macos.
MPAS_DIR=$(cd "$(dirname "$(readlink -f -n "${BASH_SOURCE[0]}" )" )" && pwd -P)
MACHINE_SETUP=${MPAS_DIR}/src/UFS_UTILS/sorc/machine-setup.sh
BUILD_DIR="${BUILD_DIR:-${MPAS_DIR}/build}"
INSTALL_DIR=${INSTALL_DIR:-$MPAS_DIR}
CONDA_BUILD_DIR="$(readlink -f "${CONDA_BUILD_DIR}")"
echo ${CONDA_BUILD_DIR} > ${MPAS_DIR}/conda_loc

if [ -z "${COMPILER}" ] ; then
  case ${PLATFORM} in
    jet|hera) COMPILER=intel ;;
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
if [ ! -f "${MPAS_DIR}/modulefiles/${MODULE_FILE}.lua" ]; then
  printf "ERROR: module file does not exist for platform/compiler\n" >&2
  printf "  MODULE_FILE=${MODULE_FILE}\n" >&2
  printf "  PLATFORM=${PLATFORM}\n" >&2
  printf "  COMPILER=${COMPILER}\n\n" >&2
  printf "Please make sure PLATFORM and COMPILER are set correctly\n" >&2
  usage >&2
  exit 64
fi

printf "MODULE_FILE=${MODULE_FILE}\n" >&2

# if build directory already exists then exit
if [ "${REMOVE}" = true ]; then
  printf "Remove build directory\n"
  printf "  BUILD_DIR=${BUILD_DIR}\n\n"
  rm -rf ${BUILD_DIR}
elif [ "${CONTINUE}" = true ]; then
  printf "Continue build in directory\n"
  printf "  BUILD_DIR=${BUILD_DIR}\n\n"
else
  if [ -d "${BUILD_DIR}" ]; then
    while true; do
      if [[ $(ps -o stat= -p ${LCL_PID}) != *"+"* ]] ; then
        printf "ERROR: Build directory already exists\n" >&2
        printf "  BUILD_DIR=${BUILD_DIR}\n\n" >&2
        usage >&2
        exit 64
      fi
      # interactive selection
      printf "Build directory (${BUILD_DIR}) already exists\n"
      printf "Please choose what to do:\n\n"
      printf "[R]emove the existing directory\n"
      printf "[C]ontinue building in the existing directory\n"
      printf "[Q]uit this build script\n"
      read -p "Choose an option (R/C/Q):" choice
      case ${choice} in
        [Rr]* ) rm -rf ${BUILD_DIR}; break ;;
        [Cc]* ) break ;;
        [Qq]* ) exit ;;
        * ) printf "Invalid option selected.\n" ;;
      esac
    done
  fi
fi

# make settings
MAKE_SETTINGS="-j ${BUILD_JOBS}"
if [ "${VERBOSE}" = true ]; then
  MAKE_SETTINGS="${MAKE_SETTINGS} VERBOSE=1"
fi

# Before we go on load modules, we first need to activate Lmod for some systems
source ${MPAS_DIR}/etc/lmod-setup.sh $MACHINE

# source the module file for this platform/compiler combination, then build the code
printf "... Load MODULE_FILE and create BUILD directory ...\n"

# load submodules
printf "...Loading MPAS-Model..."
module use ${MPAS_DIR}/src/MPAS-Model
module use ${MPAS_DIR}/modulefiles
module load ${MODULE_FILE}

module list

mkdir -p ${BUILD_DIR}
cd ${BUILD_DIR}

if [ "${CLEAN}" = true ]; then
    if [ -f $PWD/Makefile ]; then
       printf "... Clean executables ...\n"
       make ${MAKE_SETTINGS} clean 2>&1 | tee log.make
    fi
fi

exit 0
