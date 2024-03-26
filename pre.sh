
scrfunc_fp=$( readlink -f "${BASH_SOURCE[0]}" )
scrfunc_dir=$( dirname "${scrfunc_fp}" )

module use $scrfunc_dir/modulefiles
module load wflow_jet

conda activate DEV-uwtools

