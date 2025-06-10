#!/bin/bash -e

create_conda_envs () {
  . $CONDA_DIR/etc/profile.d/conda.sh
  conda activate
  if ! conda env list | grep -q "^mpas_app\s"; then
    echo "=> Creating mpas_app conda environment"
    mamba env create -y -n mpas_app --file environment.yml
  fi
  if ! conda env list | grep -q "^ungrib\s"; then
    echo "=> Creating ungrib conda environment"
    mamba create -y -n ungrib -c maddenp ungrib
  fi
}

install_conda () {
  test -d $CONDA_DIR && return
  echo "=> Installing conda"
  (
    os=$(uname)
    test $os == Darwin && os=MacOSX
    hardware=$(uname -m)
    installer=Miniforge3-$os-$hardware.sh
    version=25.3.0-3
    curl -sSLO https://github.com/conda-forge/miniforge/releases/download/$version/$installer
    bash $installer -bfp $CONDA_DIR
    rm -v $installer
    cat <<EOF >$CONDA_DIR/.condarc
channels: [conda-forge]
notify_outdated_conda: false
EOF
  )
  echo $CONDA_DIR >$MPAS_APP_DIR/conda_loc
}

install_mpas () {
  local component opts PREFIX
  component="${1:-}"
  if [[ $component == init ]]; then
    test $ATMOS_ONLY == true && return
    export PREFIX=init_
  elif [[ $component == model ]]; then
    unset PREFIX
  else
    echo "Call ${FUNCNAME[0]} with either 'init' or 'model'"
    exit 1
  fi
  echo "=> Building MPAS ${PREFIX}atmosphere"
  (
    cd $MPAS_APP_DIR/src/MPAS-Model
    test $COMPILER == gnu && build_target=gfortran
    . $MPAS_APP_DIR/etc/lmod-setup.sh $PLATFORM
    module purge
    module use $MPAS_APP_DIR/modulefiles
    module load $MODULE_NAME
    module list
    make clean CORE=atmosphere
    make clean CORE=init_atmosphere
    opts="-j $BUILD_JOBS"
    test $AUTOCLEAN == true && opts+=" AUTOCLEAN=true"
    test $DEBUG == true && opts+=" DEBUG=true"
    test $GEN_F90 == true && opts+=" GEN_F90=true"
    test $OPENMP == true && opts+=" OPENMP=true"
    test $SINGLE_PRECISION == true && opts+=" PRECISION=single"
    test -n "$TIMER_LIB" && opts+=" TIMER_LIB=$TIMER_LIB"
    test $TAU == true && opts+=" TAU=true"
    test $USE_PAPI == true && opts+=" USE_PAPI=true"
    test $VERBOSE == true && opts+=" VERBOSE=1"
    make ${build_target:-intel-mpi} CORE=${PREFIX}atmosphere $opts
    mkdir -pv $EXEC_DIR
    cp -v ${PREFIX}atmosphere_model $EXEC_DIR
    if [[ $component == model ]]; then
      ./build_tables_tempo
    fi
  )
}

install_mpassit () {
  echo "=> Building MPASSIT"
  (
    cd $MPAS_APP_DIR/src/MPASSIT
    module purge
    compiler=intel
    test $PLATFORM == ursa && compiler=intel-llvm
    ./build.sh $PLATFORM $compiler
    mkdir -pv $EXEC_DIR
    cp -v bin/mpassit $EXEC_DIR
  )
}

install_upp () {
  test $PLATFORM == ursa && return
  echo "=> Building UPP"
  (
    . $MPAS_APP_DIR/etc/lmod-setup.sh $PLATFORM
    module purge
    module use $MPAS_APP_DIR/src/UPP/modulefiles
    module load $PLATFORM
    d=$MPAS_APP_DIR/build_upp
    mkdir -pv $d
    cd $d
    args=(
      -DCMAKE_INSTALL_PREFIX=$MPAS_APP_DIR
      -DCMAKE_INSTALL_BINDIR=exec
      -DBUILD_WITH_WRFIO=ON
      $MPAS_APP_DIR/src/UPP/
    )
    cmake ${args[*]} 
    make -j $BUILD_JOBS
    make install
  )
}

show_settings () {
  cat << EOF_SETTINGS
  Settings:

    ATMOS_ONLY=$ATMOS_ONLY
    AUTOCLEAN=$AUTOCLEAN
    BUILD_JOBS=$BUILD_JOBS
    COMPILER=$COMPILER
    CONDA_DIR=$CONDA_DIR
    DEBUG=$DEBUG
    EXEC_DIR=$EXEC_DIR
    GEN_F90=$GEN_F90
    MPAS_APP_DIR=$MPAS_APP_DIR
    OPENMP=$OPENMP
    PLATFORM=$PLATFORM
    SINGLE_PRECISION=$SINGLE_PRECISION
    TAU=$TAU
    USE_PAPI=$USE_PAPI
    VERBOSE=$VERBOSE

EOF_SETTINGS
}

usage () {
cat << EOF_USAGE
Usage: $0 --platform=PLATFORM [OPTIONS] 

OPTIONS
  -h, --help
      show this help guide
  -p, --platform=PLATFORM
      name of machine you are building on
      (e.g. hera | hercules | jet | ursa)
  -c, --compiler=COMPILER
      compiler to use; default depends on platform
      (e.g. gcc | gnu | intel)
  --continue
      continue with existing build
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
      builds with default single-precision real kind. Default is to use double-precision
EOF_USAGE
}

usage_error () {
  echo "ERROR: $1"
  usage
  exit 1
}

# Initial/default settings:

export ATMOS_ONLY=false
export AUTOCLEAN=false
export BUILD_JOBS=4
export COMPILER=""
export CONDA_DIR=$(readlink -f ./conda)
export DEBUG=false
export GEN_F90=false
export OPENMP=false
export SINGLE_PRECISION=false
export TAU=false
export USE_PAPI=false
export VERBOSE=false

# Derived settings:

export MPAS_APP_DIR=$(dirname $(readlink -f ${BASH_SOURCE[0]}))
export EXEC_DIR=${EXEC_DIR:-$MPAS_APP_DIR/exec}

# Process optional arguments:

while :; do
  case $1 in
    --help|-h) usage; exit 0 ;;
    --platform=?*|-p=?*) PLATFORM=${1#*=} ;;
    --platform|--platform=|-p|-p=) usage_error "$1 requires argument." ;;
    --compiler=?*|-c=?*) COMPILER=${1#*=} ;;
    --compiler|--compiler=|-c|-c=) usage_error "$1 requires argument." ;;
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

# Validate/update platform settings:

PLATFORM=$(echo $PLATFORM | tr '[A-Z]' '[a-z]')
test -z "$PLATFORM" && usage_error "ERROR: Please set PLATFORM."

# Validate/update compiler settings:

COMPILER=$(echo $COMPILER | tr '[A-Z]' '[a-z]')
if [[ -z "$COMPILER" ]]; then
  case $PLATFORM in
    hera|hercules|jet)
      COMPILER=intel
      ;;
    *)
      COMPILER=intel
      echo WARNING: Setting default COMPILER=intel for new platform $PLATFORM
      ;;
  esac
fi
test $COMPILER == gcc && COMPILER=gnu

# Validate/update module-file settings:

export MODULE_NAME="build_${PLATFORM}_$COMPILER"
test $PLATFORM == ursa && MODULE_NAME+=_ifort
module_path=$MPAS_APP_DIR/modulefiles/$MODULE_NAME.lua
if [[ ! -f $module_path ]]; then
  echo "ERROR: Module file '$module_path' does not exist for platform '$PLATFORM' and compiler '$COMPILER'"
  exit 1
fi

# Optionally show settings:

test $VERBOSE == true && show_settings

# Install conda and environments:

install_conda
create_conda_envs

# Build components:

install_mpas init
install_mpas model
install_mpassit
install_upp

echo "=> Ready"
