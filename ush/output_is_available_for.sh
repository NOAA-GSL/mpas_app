#!/bin/bash

forecast_dir="$1"
start_time="$2"
lead_time="$3"
output_interval="$4"

eval "check_time=\$(( 10#\$lead_time + 10#\$output_interval ))"

# 2025-08-23_06.00.00
valid_time_posix=$( date +"%Y-%m-%d_%H.%M.%S" -d "$start_time UTC+0 + $check_time hours" )

history="$forecast_dir/history.$valid_time_posix.nc"
diag="$forecast_dir/diag.$valid_time_posix.nc"

exec test -s "$history" -a -s "$diag"
