#!/bin/sh
set -xue
cd ..
source ./load_wflow_modules.sh ursa
cd ush
./experiment_gen.py workflows/hfip_2026.yaml workflows/hfip_resources.yaml workflows/hfip_reservations.yaml HFIP_2026.yaml
