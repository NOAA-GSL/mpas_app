set -eux
. "$(dirname "${BASH_SOURCE[0]}")/common.sh"
ci_conda_activate mpas_app
make format
if [[ -n "$(git status --porcelain)" ]]; then
  git --no-pager diff
  echo "UNFORMATTED CODE DETECTED"
  exit 1
fi
