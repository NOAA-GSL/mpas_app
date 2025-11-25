#!/bin/bash

set -xue

YMDH=$1
archive_dir=$2

hsi mkdir -p "$archive_dir" || true

archive="$archive_dir"/${YMDH}-upp.tar

listing=$(
    ls -1 $YMDH/upp/*/*GrbF* $YMDH/upp/*/itag \
          $YMDH/upp/000/*dat $YMDH/upp/000/*txt $YMDH/upp/000/*xml $YMDH/upp/000/params_grib2_tbl_new \
 )

htar -chpvf "$archive" $listing

echo Normal completion.
