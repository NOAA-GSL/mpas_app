#!/bin/bash

set -xue

yyyymmddhh=$1
archive_dir=$2

hsi mkdir -p "$archive_dir" || true

archive="$archive_dir"/${yyyymmddhh}-lbc.tar

listing=$( ls -1 $yyyymmddhh/mpas_lbcs/lbc.*nc )

htar -chpvf "$archive" $listing

echo Normal completion.
