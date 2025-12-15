#!/bin/bash

set -xue

yyyymmddhh=$1
archive_dir=$2

hsi mkdir -p "$archive_dir" || true

archive="$archive_dir"/${yyyymmddhh}-upp.tar

listing=$(
    ls -1 $yyyymmddhh/upp/*/*GrbF* $yyyymmddhh/upp/*/itag \
          $yyyymmddhh/upp/000/*dat $yyyymmddhh/upp/000/*txt $yyyymmddhh/upp/000/*xml $yyyymmddhh/upp/000/params_grib2_tbl_new \
 )

htar -chpvf "$archive" $listing

echo Normal completion.
