#!/usr/bin/env bash

#----------------------------------------------------------------------
# Run the pygraf graphics for all forecast lead times
#
# Variables provided by Rocoto
#
#  CONFIG_PATH
#  CYCLE
#  FCST_LOCATION
#
# Variables provided by config
#
#  FCST_LENGTH: length of forecast in hours
#  FCST_FREQUENCY: the hours between forecast output
#  MODEL_DESCRIPTOR: text to be printed in figure title
#  OUTPUT_ROOT: path to output
#  PYGRAF: location of pygraf installation
#
#----------------------------------------------------------------------


# sourcing yaml section code here is lifted from SRW ush/bash_utils/source_yaml.sh
while read -r line ; do
  # A regex to match list representations
  line=$(echo "$line" | sed -E -e "s/='\[(.*)\]'/=(\1)/" -e 's/,//g' -e 's/"//g' -e 's/None//g')
  source <( echo "${line}" )
done < <(uw config realize -i "${CONFIG_PATH}" --output-format sh --key-path graphics.config)


set -x
source $PYGRAF/../../load_wflow_modules.sh $PLATFORM
conda activate pygraf
cd $PYGRAF
args=(
  maps
  -d "${FCST_LOCATION}"
  -f 0 "${FCST_LENGTH}" "${FCST_FREQUENCY}"
  --file_type prs
  --file_tmpl COMBINED.GrbF{FCST_TIME:02d}
  --images "$PYGRAF/image_lists/hrrr_subset.yml" hourly
  -m "${MODEL_DESCRIPTOR}"
  -n "${SLURM_CPUS_ON_NODE:-12}"
  -o "${OUTPUT_ROOT}/$CYCLE/pyprd"
  -s "$CYCLE"
  -w 25
  -z "${OUTPUT_ROOT}/$CYCLE/nclprd"
)

python create_graphics.py "${args[@]}"
