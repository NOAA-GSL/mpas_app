#! /bin/bash

set -ue

module purge
module use "$TRACKER_DIR/modulefiles"
module load ursa
module load wgrib2
module load grib-util
module list

set -x

ymdh="$1"
mpas_upp=../upp
syndat_prefix="$SYNDAT_PREFIX"
fhour_start=0
fhour_step="$FHOUR_STEP"
fhour_last="$FORECAST_LENGTH"
grid="-new_grid latlon -100:3333:0.03 -10:2666:0.03"
tracker="$TRACKER_DIR/exec/gettrk.x"
mpiserial="$MPISERIAL"
mpicmd="$MPICMD"

rm -rf tracker
mkdir tracker
cd tracker

####

ulimit -s unlimited

CC=${ymdh:0:2}
YY=${ymdh:2:2}
MM=${ymdh:4:2}
DD=${ymdh:6:2}
HH=${ymdh:8:2}

syndat=${syndat_prefix}.$CC$YY
if ( ! grep -E "^.....[0-49][0-9]L ......... $CC$YY$MM$DD $HH"  $syndat > allvit ) ; then
    echo "No Atlantic storms. There is nothing to track."
    echo "Delivering an empty track."
    cat /dev/null >  mpas.trak.atcfunix
    exit 0
fi
ln -sf allvit tcvit_rsmc_storms.txt

opts='-set_grib_type c2 -new_grid_winds grid -new_grid_vectors "UGRD:VGRD" -new_grid_interpolation neighbor'

PARMlistp1="UGRD:850|UGRD:700|UGRD:500|VGRD:850|VGRD:700|VGRD:500|UGRD:10 m a|VGRD:10 m a|ABSV:850|ABSV:700|MSLET|MSLP|MSLMA|mean sea|sea level"
PARMlistp2="HGT:900|HGT:850|HGT:800|HGT:750|HGT:700|HGT:650|HGT:600|HGT:550|HGT:500|HGT:450|HGT:400"
PARMlistp3="HGT:350|HGT:300|HGT:250|HGT:200|TMP:500|TMP:450|TMP:400|TMP:350|TMP:300|TMP:250|TMP:200"
PARMlist=${PARMlistp1}"|"${PARMlistp2}"|"${PARMlistp3}

rm -f ../fort.15 # list of forecast minutes

i=0
for fhr in $( seq $fhour_start $fhour_step $fhour_last ) ; do
    i=$(( i + 1 ))
    fmin=$(( fhr * 60 ))
    printf '%4d %5d\n' $i $fmin >> fort.15
    
    grib2d=$( printf "%s/%03d/%s%02d" "$mpas_upp" $fhr "2DFLD.GrbF" $fhr )
    gribprs=$( printf "%s/%03d/%s%02d" "$mpas_upp" $fhr "PRSLEV.GrbF" $fhr )

    if [[ ! -s "$grib2d" || ! -s "$gribprs" ]] ; then
        echo "No file at time $fhr" 1>&2
        break
    fi

    latlon2d=$( printf latlon_2d_%03d.grb2 $fhr )
    latlonprs=$( printf latlon_prs_%03d.grb2 $fhr )
    final=$( printf mpas.trak.all.$CC$YY$MM$DD$HH.f$( printf %05d $fmin ) )
    
    echo wgrib2 -s $grib2d \| grep -E "'$PARMlist'" \| wgrib2 -i $grib2d $opts -new_grid latlon -100:3333:0.03 -10:2666:0.03 $latlon2d >> cmdfile1
    echo wgrib2 -s $gribprs \| grep -E "'$PARMlist'" \| wgrib2 -i $gribprs $opts -new_grid latlon -100:3333:0.03 -10:2666:0.03 $latlonprs >> cmdfile1

    echo "cat $latlon2d $latlonprs > $final ; grb2index $final $final.ix" >> cmdfile2
done

# Subset the grib files:
time $mpicmd "$mpiserial" -m cmdfile1 < /dev/null

# Merge 2d and pressure grib files. Generate index files.
time $mpicmd "$mpiserial" -m cmdfile2 < /dev/null

rm -f latlon_2d* latlon_prs*

cat<<EOF > namelist.gettrk
&datein
    inp%bcc = ${CC}
    inp%byy = ${YY}
    inp%bmm = ${MM}
    inp%bdd = ${DD}
    inp%bhh = ${HH}
    inp%model = 17
    inp%modtyp = 'regional'
    inp%lt_units = 'hours'
    inp%file_seq = 'multi'
    inp%nesttyp = 'fixed'
/

&atcfinfo
    atcfnum = 81
    atcfname = 'MPAS'
    atcfymdh = ${CC}${YY}${MM}${DD}${HH}
    atcffreq = 100
/

&trackerinfo
    trkrinfo%eastbd = 3313,
    trkrinfo%westbd = 20,
    trkrinfo%northbd = 2646,
    trkrinfo%southbd = 20,
    trkrinfo%contint = 100.0
    trkrinfo%type = 'tracker'
    trkrinfo%mslpthresh = 0.0015
    trkrinfo%use_backup_mslp_grad_check = 'y'
    trkrinfo%v850thresh = 1.5
    trkrinfo%v850_qwc_thresh = 1.0
    trkrinfo%use_backup_850_vt_check = 'y'
    trkrinfo%enable_timing = 1
    trkrinfo%gridtype = 'regional'
    trkrinfo%want_oci = .true.
    trkrinfo%out_vit = 'n'
    trkrinfo%use_land_mask = 'y'
    trkrinfo%read_separate_land_mask_file = 'n'
    trkrinfo%inp_data_type = 'grib'
    trkrinfo%gribver = 2
    trkrinfo%g2_jpdtn = 0
    trkrinfo%g2_mslp_parm_id = 198
    trkrinfo%g1_mslp_parm_id = 2
    trkrinfo%g1_sfcwind_lev_typ = 105
    trkrinfo%g1_sfcwind_lev_val = 10
    trkrinfo%max_mslp_850 = 400.0
/

&phaseinfo
    phaseflag = 'y'
    phasescheme = 'both'
    wcore_depth = 1.0
/

&structinfo
    structflag = 'n'
    ikeflag = 'n'
    radii_pctile = 95.0
    radii_free_pass_pctile = 67.0
    radii_width_thresh = 15.0
/

&fnameinfo
    gmodname = 'mpas'
    rundescr = 'trak'
    atcfdescr = 'all'
/

&cintinfo
    contint_grid_bound_check = 50.0
/

&waitinfo
    use_waitfor = 'n'
    use_per_fcst_command = 'n'
/

&netcdflist
    netcdfinfo%num_netcdf_vars = ,
    netcdfinfo%netcdf_filename = ''
    netcdfinfo%netcdf_lsmask_filename = ''
    netcdfinfo%rv850name = ''
    netcdfinfo%rv700name = ''
    netcdfinfo%u850name = ''
    netcdfinfo%v850name = ''
    netcdfinfo%u700name = ''
    netcdfinfo%v700name = ''
    netcdfinfo%z850name = ''
    netcdfinfo%z700name = ''
    netcdfinfo%mslpname = ''
    netcdfinfo%usfcname = ''
    netcdfinfo%vsfcname = ''
    netcdfinfo%u500name = ''
    netcdfinfo%v500name = ''
    netcdfinfo%u200name = ''
    netcdfinfo%v200name = ''
    netcdfinfo%tmean_300_500_name = ''
    netcdfinfo%z500name = ''
    netcdfinfo%z200name = ''
    netcdfinfo%lmaskname = ''
    netcdfinfo%z900name = ''
    netcdfinfo%z800name = ''
    netcdfinfo%z750name = ''
    netcdfinfo%z650name = ''
    netcdfinfo%z600name = ''
    netcdfinfo%z550name = ''
    netcdfinfo%z450name = ''
    netcdfinfo%z400name = ''
    netcdfinfo%z350name = ''
    netcdfinfo%z300name = ''
    netcdfinfo%time_name = ''
    netcdfinfo%lon_name = ''
    netcdfinfo%lat_name = ''
    netcdfinfo%time_units = ''
    netcdfinfo%sstname = ''
    netcdfinfo%q850name = ''
    netcdfinfo%rh1000name = ''
    netcdfinfo%rh925name = ''
    netcdfinfo%rh800name = ''
    netcdfinfo%rh750name = ''
    netcdfinfo%rh700name = ''
    netcdfinfo%rh650name = ''
    netcdfinfo%rh600name = ''
    netcdfinfo%spfh1000name = ''
    netcdfinfo%spfh925name = ''
    netcdfinfo%spfh800name = ''
    netcdfinfo%spfh750name = ''
    netcdfinfo%spfh700name = ''
    netcdfinfo%spfh650name = ''
    netcdfinfo%spfh600name = ''
    netcdfinfo%temp1000name = ''
    netcdfinfo%temp925name = ''
    netcdfinfo%temp800name = ''
    netcdfinfo%temp750name = ''
    netcdfinfo%temp700name = ''
    netcdfinfo%temp650name = ''
    netcdfinfo%temp600name = ''
    netcdfinfo%omega500name = ''
/

&parmpreflist
    user_wants_to_track_zeta700 = 'y'
    user_wants_to_track_wcirc850 = 'y'
    user_wants_to_track_wcirc700 = 'y'
    user_wants_to_track_gph850 = 'y'
    user_wants_to_track_gph700 = 'y'
    user_wants_to_track_mslp = 'y'
    user_wants_to_track_wcircsfc = 'y'
    user_wants_to_track_zetasfc = 'y'
    user_wants_to_track_thick500850 = 'n'
    user_wants_to_track_thick200500 = 'n'
    user_wants_to_track_thick200850 = 'n'
    user_wants_to_track_zeta850 = 'y'
/

&verbose
    verb = 3
    verb_g2 = 0
/

&sheardiaginfo
    shearflag = 'y'
/

&sstdiaginfo
    sstflag = 'y'
/

&gendiaginfo
    genflag = 'n'
    gen_read_rh_fields = ''
/
EOF

time $mpicmd -n 1 "$tracker" < /dev/null 2>&1 | tee tracker.log

cat fort.68 >  mpas.trak.atcfunix

echo Normal completion.
