
scrfunc_fp=$( readlink -f "${BASH_SOURCE[0]}" )
scrfunc_dir=$( dirname "${scrfunc_fp}" )

module use $scrfunc_dir/modulefiles
module load wflow_$1 > /dev/null 2>&1

conda activate DEV-uwtools
