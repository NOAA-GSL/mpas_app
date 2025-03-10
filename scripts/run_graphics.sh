#!/usr/bin/env bash

#----------------------------------------------------------------------
# Run the pygraf graphics for all forecast lead times
#----------------------------------------------------------------------


# sourcing yaml section code here is lifted from SRW ush/bash_utils/source_yaml.sh
while read -r line ; do
  # A regex to match list representations
  line=$(echo "$line" | sed -E "s/='\[(.*)\]'/=(\1)/")
  line=${line//,/}
  line=${line//\"/}
  line=${line/None/}
  source <( echo "${line}" )
done < <(uw config realize -i "${CONFIG_PATH}" --output-format sh --key-path graphics.config)

cd $PYGRAF
. pre.sh
set -x
python create_graphics.py \
  maps \
  -d ${FCST_LOCATION} \
  -f 0 ${FCST_LENGTH} 6 \
  --tiles CONUS \
  --file_type prs \
  --file_tmpl COMBINED.GrbF{FCST_TIME:02d} \
  --images $PYGRAF/image_lists/rap_subset.yml hourly \
  -m "${MODEL_DESCRIPTOR}" \
  -n ${SLURM_CPUS_ON_NODE:-12} \
  -o ${OUTPUT_ROOT}/$CYCLE/pyprd \
  -s $CYCLE \
  -w 25 \
  -z ${OUTPUT_ROOT}/$CYCLE/nclprd

