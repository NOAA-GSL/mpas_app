#! /bin/bash

set -xue

YMDH=$1
archive_dir=$2

pwd

copy_to_hpss() {
    local from="$1"
    local to="$2"
    local part="$to".part

    hsi put "$from" : "$part"
    hsi mv -f "$part" "$to"
}

hsi mkdir -p "$archive_dir" || true

# This file is too large for HTAR so we copy it to HPSS via an "hsi put"

init_nc=$( ls -1 $YMDH/forecast/*init.nc | head -1 )
init_nc_hpss="$archive_dir"/${YMDH}-$( basename ${init_nc} )

md5_nc="$init_nc".md5
md5_nc_hpss="$init_nc_hpss".md5

md5sum "$init_nc" > "$md5_nc"

copy_to_hpss "$init_nc" "$init_nc_hpss"
copy_to_hpss "$md5_nc" "$md5_nc_hpss"

echo Normal completion.
