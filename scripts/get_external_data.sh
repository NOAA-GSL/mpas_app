#!/bin/bash -eu

if [[ ${ICS_or_LBCS} == "ICS" ]] ; then
  fcst_hours=$TIME_OFFSET_HRS
  if [[ ${TIME_OFFSET_HRS} -eq 0 ]] ; then
    file_set=anl
  fi
else
  first_time=$((TIME_OFFSET_HRS + LBC_INTVL_HRS))
  last_time=$((TIME_OFFSET_HRS + FCST_LEN))
  fcst_hours="${first_time} ${last_time} ${LBC_INTVL_HRS}"
fi

set -x
python -u ${MPAS_APP}/ush/retrieve_data.py \
    --debug \
    --fileset ${fileset:-fcst} \
    --config ${MPAS_APP}/parm/data_locations.yml \
    --cycle ${YYYYMMDDHH} \
    --data-stores aws \
    --data-type ${EXTERNAL_MODEL} \
    --fcst-hrs $fcst_hours \
    --filefmt grib2 \
    --output-path ${OUTPUT_PATH}

