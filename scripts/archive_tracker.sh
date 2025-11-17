#! /bin/bash

set -xue

YMDH=$1
archive_dir=$2

archive="$archive_dir"/${YMDH}-tracker.tar
htar -hcpvf "$archive" $YMDH/tracker/*

echo Normal completion.
