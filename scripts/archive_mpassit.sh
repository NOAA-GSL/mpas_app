#!/bin/bash

set -xue

day=$1
YMDH=$2
archive_dir=$3

skip_hours=$(( ( day - 1 ) * 24 ))

YYYY=${YMDH:0:4}
MM=${YMDH:4:2}
DD=${YMDH:6:2}
HH=${YMDH:8:2}

day_prefix=$( date +"MPAS-A_out.%Y-%m-%d" -d "${YYYY}-${MM}-${DD}t00:00:00 UTC+0 + $skip_hours hours" )
archive_basename=${YMDH}-mpassit-$( date +"%Y%m%d" -d "${YYYY}-${MM}-${DD}t00:00:00 UTC+0 + $skip_hours hours" ).tar

archive="$archive_dir/$archive_basename"

set +e
listing=$( ls -1 $YMDH/mpassit/*/"$day_prefix"* )
set -e

if [[ -z "${listing:-}" ]] ; then
    echo "No files to archive for day $day_prefix this cycle"
    exit 0
fi

hsi mkdir -p "$archive_dir" || true

htar -hcpvf "$archive" $listing

echo Normal completion.
