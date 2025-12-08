#!/bin/bash

set -uex

ymdh="$1"
mpicmd="$2"
fhr=$(( "10#$3" ))
new_grid="$4"
mpas_app="$5"

set +x
module load wgrib2
module load grib-util
module list
set -x

mkdir tracker || true
cd tracker

cc=${ymdh:0:2}
yy=${ymdh:2:2}
mm=${ymdh:4:2}
dd=${ymdh:6:2}
hh=${ymdh:8:2}

mpas_upp=../upp/

opts='-set_grib_type c2 -new_grid_winds grid -new_grid_vectors "UGRD:VGRD" -new_grid_interpolation neighbor'

PARMlistp1="UGRD:850|UGRD:700|UGRD:500|VGRD:850|VGRD:700|VGRD:500|UGRD:10 m a|VGRD:10 m a|ABSV:850|ABSV:700|MSLET|MSLP|MSLMA|mean sea|sea level"
PARMlistp2="HGT:900|HGT:850|HGT:800|HGT:750|HGT:700|HGT:650|HGT:600|HGT:550|HGT:500|HGT:450|HGT:400"
PARMlistp3="HGT:350|HGT:300|HGT:250|HGT:200|TMP:500|TMP:450|TMP:400|TMP:350|TMP:300|TMP:250|TMP:200"
PARMlist="${PARMlistp1}|${PARMlistp2}|${PARMlistp3}"

fmin=$(( fhr * 60 ))
grib2d=$( printf "%s/%03d/%s%02d" "$mpas_upp" $fhr "2DFLD.GrbF" $fhr )
gribprs=$( printf "%s/%03d/%s%02d" "$mpas_upp" $fhr "PRSLEV.GrbF" $fhr )

if [[ ! -s "$grib2d" || ! -s "$gribprs" ]] ; then
    echo "No file at time $fhr" 1>&2
    exit 2
fi

latlon2d=$( printf latlon_2d_%03d.grb2 $fhr )
latlonprs=$( printf latlon_prs_%03d.grb2 $fhr )
final=$( printf "mpas.trak.all.%s.f%05d" "$cc$yy$mm$dd$hh" "$fmin" )

wgrib2 -s "$grib2d" | grep -E "$PARMlist" > "$latlon2d.i"
$mpicmd -n 1 wgrib2 -i "$grib2d" $opts -new_grid $new_grid "$latlon2d" < "$latlon2d.i"

wgrib2 -s "$gribprs" | grep -E "$PARMlist" > "$latlonprs.i"
$mpicmd -n 1 wgrib2 -i "$gribprs" $opts -new_grid $new_grid "$latlonprs" < "$latlonprs.i"

cat "$latlon2d" "$latlonprs" > "$final"
grb2index "$final" "$final.ix"
