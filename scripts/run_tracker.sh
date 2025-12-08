#!/bin/bash

set -uex

ymdh="$1"
syndat_prefix="$2"
mpicmd="$3"
fhour_step="$4" # 6
fhour_last="$5" # 120
mpas_app="$6"
eastbd="$7" # 3313
westbd="$8" # 20
northbd="$9" # 2646
southbd="${10}" # 20
atcfname="${11}" # MPAS
basin_list="${12}" # L
platform="${13}" # ursa

mpas_upp=../upp
fhour_start=0

tracker="$mpas_app/exec/gettrk.x"

cd tracker

valid_basins='ABCELPQSW'
if [[ ! "$basin_list" =~ [$valid_basins] ]] ; then
    set +x
    echo "Invalid basin in list \"$basin_list\". Valid basins are: \"$valid_basins\" (Q is exceptionally rare)."
    exit 2
fi

# Some sanity checks. More could be added, but these detected my mistakes.
min_width_height=80
if ! [[ "$eastbd$westbd$northbd$southbd" =~ [0-9]+ ]] ; then
    set +x
    echo "Bounds must all be positive numbers. Got: east=$eastbd west=$westbd north=$northbd south=$southbd"
    exit 2
elif (( eastbd < westbd )) ; then
    set +x
    echo "East and west bound are probably switched. East bound ($eastbd) is less than west bound ($westbd)"
    exit 2
elif (( eastbd < westbd+min_width_height )) ; then
    set +x
    echo "East and west bound are close together ($eastbd vs $westbd). Recommend at least $min_width_height points."
    exit 2
elif (( northbd < southbd )) ; then
    set +x
    echo "North and south bound are probably switched. North bound ($northbd) is less than south bound ($southbd)."
    exit 2
elif (( northbd < southbd+min_width_height )) ; then
    set +x
    echo "North and south bound are close together. Recommend at least $min_width_height points."
    exit 2
fi

rm -f fort.*
rm -f *.atcfunix
rm -f allvit tcvit_rsmc_storms.txt tracker.log

####

ulimit -s unlimited

cc=${ymdh:0:2}
yy=${ymdh:2:2}
mm=${ymdh:4:2}
dd=${ymdh:6:2}
hh=${ymdh:8:2}

syndat=${syndat_prefix}.$cc$yy
if ( ! grep -E "^.....[0-49][0-9][$basin_list] ......... $cc$yy$mm$dd $hh"  $syndat > allvit ) ; then
    echo "No storms in basin list \"$basin_list\". There is nothing to track."
    echo "Delivering an empty track."
    cat /dev/null >  mpas.trak.atcfunix
    exit 0
fi

ln -sf allvit tcvit_rsmc_storms.txt

i=0
for fhr in $( seq $fhour_start $fhour_step $fhour_last ) ; do
    i=$(( i + 1 ))
    fmin=$(( fhr * 60 ))
    printf '%4d %5d\n' $i $fmin >> fort.15
done

cat<<EOF > namelist.gettrk
&datein
    inp%bcc = ${cc}
    inp%byy = ${yy}
    inp%bmm = ${mm}
    inp%bdd = ${dd}
    inp%bhh = ${hh}
    inp%model = 17
    inp%modtyp = 'regional'
    inp%lt_units = 'hours'
    inp%file_seq = 'multi'
    inp%nesttyp = 'fixed'
/

&atcfinfo
    atcfnum = 81
    atcfname = '$atcfname'
    atcfymdh = ${cc}${yy}${mm}${dd}${hh}
    atcffreq = 100
/

&trackerinfo
    trkrinfo%eastbd = $eastbd,
    trkrinfo%westbd = $westbd,
    trkrinfo%northbd = $northbd,
    trkrinfo%southbd = $southbd,
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
