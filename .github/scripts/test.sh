set -eu
source conda/etc/profile.d/conda.sh
conda activate mpas_app
conda info
set -x
sleep 10
conda list
echo $PATH
which ruff
git clean -dfx
make test
