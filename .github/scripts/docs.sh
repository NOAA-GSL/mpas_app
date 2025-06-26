set -eu
source conda/etc/profile.d/conda.sh
conda activate mpas_app
set -x
source docs/install-deps
make docs
