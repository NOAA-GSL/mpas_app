#!/bin/bash -e

# Functions:

create_conda_envs () {
  source $CONDA_DIR/etc/profile.d/conda.sh
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

export_var_defaults () {

  export MPAS_APP_DIR=$(dirname $(readlink -f ${BASH_SOURCE[0]}))
  export MODULE_NAME=

  # Defaults for CLI options:

  export ATMOS_ONLY=false
  export BUILD_JOBS=4
  export COMPILER=
  export CONDA_DIR=$MPAS_APP_DIR/conda
  export DEBUG=false
  export EXEC_DIR=$MPAS_APP_DIR/exec
  export GEN_F90=false
  export OPENMP=false
  export PLATFORM=
  export SINGLE_PRECISION=false
  export TAU=false
  export TIMER_LIB=
  export USE_PAPI=false
  export VERBOSE=false

}

fail () {
  echo $1
  exit 1
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
  local CORE errmsg
  errmsg="BUG: ${FUNCNAME[0]} takes 'init_atmosphere' or 'atmosphere'"
  test $# -eq 1 || fail "$errmsg"
  export CORE="${1:-}"
  if [[ $CORE == init_atmosphere ]]; then
    test $ATMOS_ONLY == true && return
  elif [[ $CORE != atmosphere ]]; then
    fail "$errmsg"
  fi
  echo "=> Building MPAS $CORE"
  (
    cd $MPAS_APP_DIR/src/MPAS-Model
    test $COMPILER == gnu && build_target=gfortran
    source $MPAS_APP_DIR/etc/lmod-setup.sh $PLATFORM
    module purge
    module use $MPAS_APP_DIR/modulefiles
    module load $MODULE_NAME
    module list
    make clean CORE=atmosphere
    make clean CORE=init_atmosphere
    opts="-j $BUILD_JOBS"
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
    cp -v ${CORE}_model $EXEC_DIR
    test $CORE == atmosphere && ./build_tables_tempo || true
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
    source $MPAS_APP_DIR/etc/lmod-setup.sh $PLATFORM
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

prepare_conda () {
  install_conda
  create_conda_envs
}

prepare_shell () {
  export_var_defaults
  process_cli_args $@
  validate_and_update_vars
}

process_cli_args () {
  local long name opts
  long=atmos-only,build-jobs:,compiler:,conda-dir:,debug,exec-dir:,gen-f90,help,openmp,platform:,single-precision,tau,timer-lib:,use-papi
  name=$(basename ${BASH_SOURCE[0]})
  opts=$(getopt -n $name -o c:hp:v -l $long -- "$@") || usage_error
  eval set -- $opts
  while true; do
    case $1 in
      --help|-h)          usage && exit 0        ;;
      --atmos-only)       ATMOS_ONLY=true        ;;
      --build-jobs)       BUILD_JOBS=$2 && shift ;;
      --compiler|-c)      COMPILER=$2 && shift   ;;
      --conda-dir)        CONDA_DIR=$2 && shift  ;;
      --debug)            DEBUG=true             ;;
      --exec-dir)         EXEC_DIR=$2 && shift   ;;
      --gen-f90)          GEN_F90=true           ;;
      --openmp)           OPENMP=true            ;;
      --platform|-p)      PLATFORM=$2 && shift   ;;
      --single-precision) SINGLE_PRECISION=true  ;;
      --tau)              TAU=true               ;;
      --timer-lib)        TIMER_LIB=$2 && shift  ;;
      --use-papi)         USE_PAPI=true          ;;
      --verbose|-v)       VERBOSE=true           ;;
      --)                 break                  ;;
    esac
    shift
  done
}

show_settings () {
  cat << EOF_SETTINGS
  Settings:

    ATMOS_ONLY=$ATMOS_ONLY
    BUILD_JOBS=$BUILD_JOBS
    COMPILER=$COMPILER
    CONDA_DIR=$CONDA_DIR
    DEBUG=$DEBUG
    EXEC_DIR=$EXEC_DIR
    GEN_F90=$GEN_F90
    OPENMP=$OPENMP
    PLATFORM=$PLATFORM
    SINGLE_PRECISION=$SINGLE_PRECISION
    TAU=$TAU
    TIMER_LIB=$TIMER_LIB
    USE_PAPI=$USE_PAPI
    VERBOSE=$VERBOSE

EOF_SETTINGS
}

usage () {
  cat << EOF
Usage: $0 --platform PLATFORM [OPTIONS]

OPTIONS
  -c, --compiler COMPILER (choices: gcc, gnu, intel)
      compiler to use (default: depends on platform)
  -h, --help
      show this help guide
  -p, --platform PLATFORM (choices: hera, hercules, jet, ursa)
      system where build is being performed
  -v, --verbose
      build with verbose output
  --atmos-only
      do not built init_atmosphere core, only atmosphere
  --build-jobs BUILD_JOBS
      number of build jobs (default: 4)
  --conda-dir CONDA_DIR
      directory to install conda info (default: conda/ under MPAS App)
  --debug
      build MPAS in debug mode
  --exec-dir EXEC_DIR
      directory to install executables into (default: exec/ under MPAS App)
  --openmp
      build with OpenMP support
  --single-precision
      build with single-precision reals, not default double-precision
  --tau
      builds MPAS with TAU profiling hooks
  --timer-lib TIMER_LIB
      timer library interface to use for profiling MPAS (choices: gptl, native, tau)
  --use-papi
      build MPAS with PAPI timers
EOF
}

usage_error () {
  test -n "$1" && echo "ERROR: $1"
  usage
  exit 1
}

validate_and_update_vars () {

  local module_path

  # Validate/update platform settings:

  PLATFORM=$(echo $PLATFORM | tr '[A-Z]' '[a-z]')
  test -z "$PLATFORM" && usage_error "Please specify platform"

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

  MODULE_NAME="build_${PLATFORM}_$COMPILER"
  test $PLATFORM == ursa && MODULE_NAME+=_ifort
  module_path=$MPAS_APP_DIR/modulefiles/$MODULE_NAME.lua
  if [[ ! -f $module_path ]]; then
    echo "ERROR: Module file '$module_path' not found for platform '$PLATFORM' and compiler '$COMPILER'"
    exit 1
  fi

  # Optionally show settings:

  test $VERBOSE == true && show_settings || true
}

# Top-level logic:

echo "=> Building"
prepare_shell $@
prepare_conda
install_mpas init_atmosphere
install_mpas atmosphere
install_mpassit
install_upp
echo "=> Ready"
