set -eu
source conda/etc/profile.d/conda.sh
conda activate mpas_app
set -x
make format
if [[ -n "$(git status --porcelain)" ]]; then
  git --no-pager diff
  echo "UNFORMATTED CODE DETECTED"
  exit 1
fi
