#!/bin/bash

forecast_dir="$1"
start_time="$2"
lead_time="$3"
add_to_lead_time="$4"

eval "check_time=\$(( 10#\$lead_time + 10#\$add_to_lead_time ))"

# 2025-08-22t00:00:00 UTC+0
s="$start_time"
start_posix="${s:0:4}-${s:5:2}-${s:8:2}t${s:11:2}:${s:14:2}:${s:17:2} UTC+0"

# 2025-08-23_06.00.00
valid_time_posix=$( date +"%Y-%m-%d_%H.%M.%S" -d "$start_posix + $check_time hours" )

history="$forecast_dir/history.$valid_time_posix.nc"
diag="$forecast_dir/diag.$valid_time_posix.nc"

exec test -s "$history" -a -s "$diag"
