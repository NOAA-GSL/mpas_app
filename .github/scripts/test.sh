set -eux
. "$(dirname "${BASH_SOURCE[0]}")/common.sh"
ci_conda_activate mpas_app
git clean -dfx
make test