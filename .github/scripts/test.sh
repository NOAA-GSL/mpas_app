set -eu
source conda/etc/profile.d/conda.sh
conda activate mpas_app
conda info
set -x
conda list
git clean -dfx
make test
