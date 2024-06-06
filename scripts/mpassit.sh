#!/bin/bash

# Default settings
MODULE_FILE="/path/to/default/modulefile"
WORK_DIR="/default/work/dir"
FCST_HOUR="00"
INIT_TIME="2023010100" # default initial time
FIX_DIR="/default/fix/dir"
NML_DIR="/default/namelist/dir"
PARM_DIR="/default/parm/dir"
EXEC_DIR="/default/exec/dir"
MP_SCHEME="mp_thompson" # default microphysics scheme
verb=0 # Verbosity

# Function to show help
usage() {
    echo "Usage: $0 [options]"
    echo "Options:"
    echo "  -m MODULE_FILE    Path to the module file to source"
    echo "  -w WORK_DIR       Work directory path"
    echo "  -f FCST_HOUR      Forecast hour"
    echo "  -i INIT_TIME      Initial time (YYYYMMDDHH format)"
    echo "  -x FIX_DIR        Directory for fixed files"
    echo "  -n NAMELIST_DIR   Directory for namelist files"
    echo "  -p PARM_DIR       Directory for parm files"
    echo "  -e EXEC_DIR       Directory for executable files"
    echo "  -s MP_SCHEME      Microphysics scheme ('mp_thompson' or 'NSSL')"
    echo "  -v                Enable verbose output"
    echo "  -h                Show this help message"
}


# Parse command-line options
while getopts "m:w:f:i:x:n:p:e:s:vh" opt; do
  case ${opt} in
    m )
      MODULE_FILE=$OPTARG
      ;;
    w )
      WORK_DIR=$OPTARG
      ;;
    f )
      FCST_HOUR=$OPTARG
      ;;
    i )
      INIT_TIME=$OPTARG
      ;;
    x )
      FIX_DIR=$OPTARG
      ;;
    n )
      NML_DIR=$OPTARG
      ;;
    p )
      PARM_DIR=$OPTARG
      ;;
    e )
      EXEC_DIR=$OPTARG
      ;;
    s )
      MP_SCHEME=$OPTARG
      ;;
    v )
      verb=1
      ;;
    h )
      usage
      exit 0
      ;;
    \? )
      echo "Invalid Option: -$OPTARG" 1>&2
      usage
      exit 1
      ;;
  esac
done

module use $( dirname "${MODULE_FILE}" )
module load $( basename ${MODULE_FILE} )
module list

set -eux
# Prepare directories and files
rm -rf $WORK_DIR/$FCST_HOUR
mkdir -p $WORK_DIR/$FCST_HOUR
cd $WORK_DIR/$FCST_HOUR

ymd=$(echo $INIT_TIME | cut -c 1-8)
h=$(echo $INIT_TIME | cut -c 9-10)

fcst_time_str=$(date -d "${ymd} ${h}:00 ${FCST_HOUR} hours" +%Y-%m-%d_%H.%M.%S)
histfile="${FCST_DIR}/history.${fcst_time_str}.nc"
diagfile="${FCST_DIR}/diag.${fcst_time_str}.nc"

fileappend=$([[ "${MP_SCHEME}" == "mp_thompson" ]] && echo "THOM" || echo "NSSL")

parmfiles=(diaglist histlist_2d histlist_3d histlist_soil)
for fn in "${parmfiles[@]}"; do
    if [[ ! -e $fn ]]; then
        if [[ $verb -eq 1 ]]; then echo "Linking $fn ..."; fi
        if [[ -e $PARM_DIR/${fn}.${fileappend} ]]; then
            ln -sf $PARM_DIR/${fn}.${fileappend} $fn
        elif [[ -e $PARM_DIR/${fn} ]]; then
            ln -sf $PARM_DIR/$fn .
        else
            echo "ERROR: file \"$PARM_DIR/${fn}\" not exist."
            exit 1
        fi
    fi
done

ln -sf $INIT_DIR/conus.init.nc .
ln -sf $EXEC_DIR/mpassit .

hstr=$(printf "%02d" $FCST_HOUR)
nmlfile="namelist.fcst_$hstr"

cp $NML_DIR/namelist.mpassit $nmlfile
sed -i "s|HISTFILE|$histfile|g" $nmlfile
sed -i "s|DIAGFILE|$diagfile|g" $nmlfile
sed -i "s|FIX_DIR|$FIX_DIR|g" $nmlfile
sed -i "s/FCSTTIME/$fcst_time_str/g" $nmlfile

srun mpassit $nmlfile

outfile="${WORK_DIR}/${FCST_HOUR}/MPAS-A_out.${fcst_time_str}.nc"
if [[ -e $outfile ]]; then
  echo "Created "${outfile}" successfully"
  exit 0
else
  echo "Failed to create "${outfile}
  exit 1
fi
