#!/bin/bash -eu

if [[ ${ICS_or_LBCS} == "ICS" ]] ; then
  fcst_hours=$TIME_OFFSET_HRS
  if [[ ${TIME_OFFSET_HRS} -eq 0 ]] ; then
    fileset=anl
  fi
else
  first_time=$((TIME_OFFSET_HRS + LBC_INTVL_HRS))
  last_time=$((TIME_OFFSET_HRS + FCST_LEN))
  fcst_hours="${first_time} ${last_time} ${LBC_INTVL_HRS}"
fi

args=(
  --debug
  --fileset ${fileset:-fcst}
  --config $MPAS_APP/parm/data_locations.yml
  --cycle $cycle
  --data-stores $DATA_STORES
  --data-type $EXTERNAL_MODEL
  --fcst-hrs $fcst_hours
  --filefmt grib2
  --output-path $OUTPUT_PATH
  --summary-file $OUTPUT_PATH/$ICS_or_LBCS.yaml
)
if [[ -n "${INPUT_FILE_PATH:-}" ]]; then
  args+=(--input-file-path "$INPUT_FILE_PATH")
fi
if [[ -n "${FILE_TEMPLATES:-}" ]]; then
  args+=(--file-templates "$FILE_TEMPLATES")
fi
set -x
python -u $MPAS_APP/ush/retrieve_data.py "${args[@]}"
