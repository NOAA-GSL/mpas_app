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
    --file_set ${file_set:-fcst} \
    --config ${MPAS_APP}/parm/data_locations.yml \
    --cycle_date ${YYYYMMDDHH} \
    --data_stores aws \
    --data_type RAP \
    --fcst_hrs $fcst_hours \
    --file_fmt grib2 \
    --ics_or_lbcs ${ICS_or_LBCS} \
    --output_path ${OUTPUT_PATH}

