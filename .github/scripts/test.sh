set -eu
source conda/etc/profile.d/conda.sh
conda activate mpas_app
set -x
git clean -dfx
make test
