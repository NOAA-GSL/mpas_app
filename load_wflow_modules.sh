
scrfunc_fp=$( readlink -f "${BASH_SOURCE[0]}" )
scrfunc_dir=$( dirname "${scrfunc_fp}" )

source $scrfunc_dir/etc/lmod-setup.sh
module use $scrfunc_dir/modulefiles
module load wflow_$1 > /dev/null 2>&1

conda activate mpas_app
