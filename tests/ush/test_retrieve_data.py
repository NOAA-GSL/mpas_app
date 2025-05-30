import argparse
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import call, patch

from pytest import fixture, mark, raises
from uwtools.api.config import YAMLConfig, get_yaml_config

from ush import retrieve_data


@fixture
def data_locations():
    return get_yaml_config(Path(f"{__file__}/../../../parm/data_locations.yml").resolve())


@fixture
def sysargs(tmp_path):
    return [
        "--fileset",
        "fcst",
        "--config",
        str(Path(f"{__file__}/../../../parm/data_locations.yml").resolve()),
        "--cycle",
        "2025-05-04T00",
        "--data-stores",
        "disk",
        "hpss",
        "--data-type",
        "GFS",
        "--fcst-hrs",
        "6",
        "12",
        "3",
        "--input-file-path",
        str(tmp_path / "input"),
        "--output-path",
        str(tmp_path),
        "--debug",
        "--filefmt",
        "grib2",
    ]


def test_import():
    assert retrieve_data


def test__abort(capsys):
    msg = "exit from _abort"
    with raises(SystemExit) as e:
        retrieve_data._abort(msg)
    assert e.value.code == 1
    assert msg in capsys.readouterr().err


@mark.parametrize(
    ("inargs", "expected"),
    [
        ([0], [0]),
        ([2, 5], [2, 3, 4, 5]),
        ([3, 4, 5, 6], [3, 4, 5, 6]),
        ([0, 12, 6], [0, 6, 12]),
        ("0 12 6", [0, 6, 12]),
        ("12    13 14  22", [12, 13, 14, 22]),
    ],
)
def test__arg_list_to_range_list(expected, inargs):
    result = retrieve_data._arg_list_to_range(inargs)
    assert result == expected


def test__timedelta_from_str(capsys):
    assert (
        retrieve_data._timedelta_from_str("111:222:333").total_seconds()
        == 111 * 3600 + 222 * 60 + 333
    )
    assert retrieve_data._timedelta_from_str("111:222").total_seconds() == 111 * 3600 + 222 * 60
    assert retrieve_data._timedelta_from_str("111").total_seconds() == 111 * 3600
    assert retrieve_data._timedelta_from_str("01:15:07").total_seconds() == 1 * 3600 + 15 * 60 + 7
    with raises(SystemExit):
        retrieve_data._timedelta_from_str("foo")
    assert "Specify leadtime as hours[:minutes[:seconds]]" in capsys.readouterr().err


def test_get_filenames_filefmt():
    files = {"anl": {"grib2": ["file1.txt", "file2.txt"]}}
    result = retrieve_data.get_filenames(filename_config=files, filefmt="grib2", fileset="anl")
    assert result == files["anl"]["grib2"]


def test_get_filenames_no_filefmt():
    files = {"anl": ["file1.txt", "file2.txt"]}
    result = retrieve_data.get_filenames(filename_config=files, filefmt="foo", fileset="anl")
    assert result == files["anl"]


def test_main(tmp_path):
    # Using a basic YAML here while UW-suported YAML tags are not comparable.
    config = tmp_path / "data_locations.yml"
    config.write_text("foo: bar")
    cycle = "2025-05-04T00"
    cycle_dt = datetime.fromisoformat(cycle).replace(tzinfo=timezone.utc)
    args = [
        "--fileset",
        "fcst",
        "--config",
        str(config),
        "--cycle",
        cycle,
        "--data-stores",
        "aws",
        "--data-type",
        "GFS",
        "--fcst-hrs",
        "6",
        "12",
        "3",
        "--output-path",
        str(tmp_path),
        "--filefmt",
        "grib2",
    ]
    with patch.object(retrieve_data, "retrieve_data") as retrieve:
        retrieve_data.main(args)
    expected_args = dict(
        config=get_yaml_config(str(config)),
        cycle=cycle_dt,
        data_stores=["aws"],
        data_type="GFS",
        fileset="fcst",
        filefmt="grib2",
        lead_times=[timedelta(hours=i) for i in (6, 9, 12)],
        file_templates=[],
        inpath=None,
        members=[-999],
        outpath=tmp_path,
        summary_file=None,
        symlink=False,
    )
    retrieve.assert_called_with(**expected_args)


def test_parse_args_hsi_available(sysargs, tmp_path):
    with patch(
        "ush.retrieve_data.subprocess.run",
        side_effect=[subprocess.CompletedProcess(args="/usr/bin/which hsi", returncode=0)],
    ):
        args = retrieve_data.parse_args(sysargs)
    assert args.fileset in retrieve_data.FILE_SETS
    assert isinstance(args.config, YAMLConfig)
    assert isinstance(args.cycle, datetime)
    assert isinstance(args.data_stores, list)
    assert all(ds in ["hpss", "nomads", "aws", "disk"] for ds in args.data_stores)
    assert args.data_type is not None
    assert args.fcst_hrs == [timedelta(hours=h) for h in (6, 9, 12)]
    assert args.output_path.is_absolute()
    assert not args.symlink
    assert args.debug
    assert args.file_templates == []
    assert args.filefmt in ("grib2", "nemsio", "netcdf", "prepbufr", "tcvitals")
    assert args.input_file_path == tmp_path / "input"
    assert args.members == [-999]
    assert args.summary_file is None


def test_parse_args_hsi_not_available(sysargs):
    with (
        patch(
            "ush.retrieve_data.subprocess.run",
            side_effect=subprocess.CalledProcessError(cmd="foo", returncode=1),
        ),
        raises(SystemExit),
    ):
        retrieve_data.parse_args(sysargs)


def test_parse_args_no_filefmt(sysargs):
    for arg in ("--filefmt", "grib2"):
        sysargs.remove(arg)
    with patch(
        "ush.retrieve_data.subprocess.run",
        side_effect=[subprocess.CompletedProcess(args="/usr/bin/which hsi", returncode=0)],
    ):
        args = retrieve_data.parse_args(sysargs)
    assert isinstance(args.filefmt, str)


def test_parse_args_no_input_path_for_disk(sysargs, tmp_path):
    sysargs.remove("--input-file-path")
    sysargs.remove(str(tmp_path / "input"))
    with raises(argparse.ArgumentTypeError):
        retrieve_data.parse_args(sysargs)


def test_possible_hpss_configs(data_locations):
    leads = (6, 12)
    cycle = datetime.fromisoformat("2025-05-04T00").replace(tzinfo=timezone.utc)
    lead_times = [timedelta(hours=lead) for lead in leads]

    expected1 = {
        "gfs.t00z.pgrb2.0p25.f000": "htar:///NCEPPROD/hpssprod/runhistory/rh2025/202505/20250504/gpfs_dell1_nco_ops_com_gfs_prod_gfs.20250504_00.gfs_pgrb2.tar?./gfs.20250504/00/gfs.t00z.pgrb2.0p25.f000"
    }

    expected2 = {
        "gfs.t00z.pgrb2.0p25.f000": "htar:///NCEPPROD/hpssprod/runhistory/rh2025/202505/20250504/com_gfs_prod_gfs.20250504_00.gfs_pgrb2.tar?./gfs.20250504/00/gfs.t00z.pgrb2.0p25.f000"
    }

    gfs_hpss = data_locations["GFS"]["hpss"]
    config = retrieve_data.possible_hpss_configs(
        archive_locations=gfs_hpss,
        archive_names=gfs_hpss["archive_filenames"]["anl"]["grib2"],
        config=data_locations,
        cycle=cycle,
        file_templates=data_locations["GFS"]["filenames"]["anl"]["grib2"],
        lead_times=lead_times,
        members=[-999],
    )

    def _count_iterator(iterator):
        count = 0
        for _ in iterator:
            count += 1
        return count

    assert next(config) == expected1
    assert next(config) == expected2
    assert _count_iterator(config) == 6  # already used first 2 of 8


def test_prepare_fs_copy_config_gefs_grib2_aws(data_locations):
    members = [2, 3]
    cycle = datetime.fromisoformat("2025-05-04T00").replace(tzinfo=timezone.utc)
    lead_times = [timedelta(hours=0)]
    expected = {
        f"mem{mem:03d}/gep{mem:02d}.t00z.{filelabel}.0p50.f000": f"https://noaa-gefs-pds.s3.amazonaws.com/gefs.{cycle.strftime('%Y%m%d')}/{cycle.hour:02d}/atmos/{filelabel}p5/gep{mem:02d}.t00z.{filelabel}.0p50.f000"
        for mem in members
        for filelabel in ("pgrb2a", "pgrb2b")
    }
    configs = retrieve_data.prepare_fs_copy_config(
        config=data_locations,
        cycle=cycle,
        file_templates=data_locations["GEFS"]["filenames"]["anl"]["grib2"],
        lead_times=lead_times,
        locations=data_locations["GEFS"]["aws"]["locations"],
        members=members,
    )
    assert configs.__next__() == expected


def test_prepare_fs_copy_config_gfs_grib2_aws(data_locations):
    leads = (6, 12)
    cycle = datetime.fromisoformat("2025-05-04T00").replace(tzinfo=timezone.utc)
    lead_times = [timedelta(hours=lead) for lead in leads]
    expected = {
        f"gfs.t{cycle.hour:02d}z.{level}f{lead:03d}.nc": f"https://noaa-gfs-bdp-pds.s3.amazonaws.com/gfs.{cycle.strftime('%Y%m%d')}/{cycle.hour:02d}/atmos/gfs.t{cycle.hour:02d}z.{level}f{lead:03d}.nc"
        for lead in leads
        for level in ("atm", "sfc")
    }
    configs = retrieve_data.prepare_fs_copy_config(
        config=data_locations,
        cycle=cycle,
        file_templates=data_locations["GFS"]["filenames"]["fcst"]["netcdf"],
        lead_times=lead_times,
        locations=data_locations["GFS"]["aws"]["locations"],
        members=[-999],
    )
    assert configs.__next__() == expected


@mark.parametrize("data_set", ["RAP", "GFS", "GDAS"])
def test_retrieve_data(data_locations, data_set, tmp_path):
    data_stores = ["disk", "aws", "hpss"]
    remove_args = ("data_stores", "data_type", "filefmt", "fileset", "inpath", "summary_file")

    cycle = datetime.fromisoformat("2025-05-04T00").replace(tzinfo=timezone.utc)
    args = {
        "config": get_yaml_config({data_set: data_locations[data_set]}),
        "cycle": cycle,
        "data_stores": data_stores,
        "data_type": data_set,
        "fileset": "fcst",
        "outpath": tmp_path / "output",
        "filefmt": "netcdf",
        "file_templates": ["a.f{{ '%3d' % fcst_hr }}.grib"],
        "lead_times": [6],
        "members": [None],
        "inpath": tmp_path / "input",
        "symlink": False,
        "summary_file": tmp_path / "summary.yaml",
    }
    with patch.object(retrieve_data, "try_data_store", return_value=(False, {})) as try_data_store:
        retrieve_data.retrieve_data(**args)
        disk_calls = args.copy()
        data_store_args = {
            "data_store": "disk",
            "locations": [tmp_path / "input"],
            "archive_config": None,
            "archive_names": None,
        }
        disk_calls.update(data_store_args)
        for key in remove_args:
            disk_calls.pop(key)

        aws_calls = args.copy()
        data_store_args = {
            "data_store": "aws",
            "file_templates": retrieve_data.get_filenames(
                data_locations[data_set].get("aws", {}).get("filenames")
                or data_locations[data_set]["filenames"],
                args["filefmt"],
                "fcst",
            ),
            "locations": data_locations[data_set]["aws"]["locations"],
            "archive_config": None,
            "archive_names": None,
        }
        aws_calls.update(data_store_args)
        for key in remove_args:
            aws_calls.pop(key)

        hpss_calls = args.copy()
        archive_names = data_locations[data_set]["hpss"]["archive_filenames"]
        if isinstance(archive_names, dict):
            archive_names = data_locations[data_set]["hpss"]["archive_filenames"]["fcst"]["netcdf"]
        data_store_args = {
            "data_store": "hpss",
            "file_templates": retrieve_data.get_filenames(
                data_locations[data_set]["filenames"], args["filefmt"], "fcst"
            ),
            "locations": data_locations[data_set]["hpss"]["locations"],
            "archive_config": data_locations[data_set]["hpss"],
            "archive_names": archive_names,
        }
        hpss_calls.update(data_store_args)
        for key in remove_args:
            hpss_calls.pop(key)
        try_data_store.assert_has_calls([call(**disk_calls), call(**aws_calls), call(**hpss_calls)])


def test_retrieve_data_summary_file(data_locations, tmp_path):
    data_stores = ["disk"]
    data_set = "GFS"
    cycle = datetime.fromisoformat("2025-05-04T00").replace(tzinfo=timezone.utc)
    summary_file = tmp_path / "summary.yaml"
    args = {
        "config": get_yaml_config({data_set: data_locations[data_set]}),
        "cycle": cycle,
        "data_stores": data_stores,
        "data_type": data_set,
        "fileset": "anl",
        "outpath": tmp_path / "output",
        "filefmt": "wgrib2",
        "file_templates": ["a.f{{ '%3d' % fcst_hr }}.grib"],
        "lead_times": [0],
        "members": [None],
        "inpath": tmp_path / "input",
        "symlink": False,
        "summary_file": summary_file,
    }
    summary = {
        "a.f000.grib": str(tmp_path / "input" / "a.f000.grib"),
    }

    with patch.object(retrieve_data, "try_data_store", return_value=(True, summary)):
        retrieved = retrieve_data.retrieve_data(**args)

    assert retrieved is True
    assert summary_file.is_file()
    assert summary_file.read_text().strip() == repr(get_yaml_config(summary))


def test_try_data_store_disk_fail(tmp_path):
    file_path = tmp_path / "{{ cycle.strftime('%Y%m%d%H') }}"
    output_path = tmp_path / "output"
    output_path.mkdir()
    tmp_file = "tmp.f{{ fcst_hr }}"
    cycle = datetime.now(tz=timezone.utc)
    lead_times = [timedelta(hours=6), timedelta(hours=12)]

    success, _ = retrieve_data.try_data_store(
        config=get_yaml_config({}),
        cycle=cycle,
        data_store="disk",
        file_templates=[tmp_file],
        lead_times=lead_times,
        locations=[file_path],
        members=[0],
        outpath=output_path,
    )
    assert not success


def test_try_data_store_disk_success(data_locations, tmp_path):
    file_path = tmp_path / "{{ cycle.strftime('%Y%m%d%H') }}"
    output_path = tmp_path / "output"
    output_path.mkdir()
    tmp_file = "tmp.f{{ fcst_hr }}"
    existing_file_template = file_path / tmp_file
    cycle = datetime.now(tz=timezone.utc)
    lead_times = [timedelta(hours=6), timedelta(hours=12)]

    new_files = []
    for lead_time in lead_times:
        file_config = get_yaml_config({"file": str(existing_file_template)})
        file_config.dereference(
            context={
                "cycle": cycle,
                "fcst_hr": int(lead_time.total_seconds() // 3600),
            }
        )
        new_file = Path(file_config["file"])
        new_file.parent.mkdir(parents=True, exist_ok=True)
        new_file.touch()
        new_files.append(new_file)

    success, _ = retrieve_data.try_data_store(
        config=data_locations,
        cycle=cycle,
        data_store="disk",
        file_templates=[tmp_file],
        lead_times=lead_times,
        locations=[file_path],
        members=[-999],
        outpath=output_path,
    )
    assert all((output_path / f.name).is_file() for f in new_files)
    assert success


def test_try_data_store_hpss(data_locations, tmp_path):
    gfs_config = data_locations["GFS"]
    cycle = datetime.now(tz=timezone.utc)
    with patch.object(
        retrieve_data, "possible_hpss_configs", return_value=iter({})
    ) as possible_hpss_configs:
        success, _ = retrieve_data.try_data_store(
            config=get_yaml_config({"GFS": gfs_config}),
            cycle=cycle,
            data_store="hpss",
            file_templates=retrieve_data.get_filenames(gfs_config["filenames"], "grib2", "anl"),
            lead_times=[timedelta(hours=0)],
            locations=gfs_config["hpss"]["locations"],
            members=[-999],
            outpath=tmp_path / "output",
            archive_config=gfs_config["hpss"],
            archive_names=retrieve_data.get_filenames(
                gfs_config["hpss"]["archive_filenames"], "grib2", "anl"
            ),
        )
    possible_hpss_configs.assert_called_once_with(
        archive_locations=gfs_config["hpss"],
        archive_names=gfs_config["hpss"]["archive_filenames"]["anl"]["grib2"],
        config={"GFS": gfs_config},
        cycle=cycle,
        file_templates=["gfs.t{{hh}}z.pgrb2.0p25.f000"],
        lead_times=[timedelta(hours=0)],
        members=[-999],
    )


# Tests that pull data


@mark.parametrize(
    ("data_set", "filefmt", "filenames"),
    [
        ("GDAS", "netcdf", ["gdas.t12z.sfcf003.nc"]),
        (
            "GEFS",
            "grib2",
            ["gep{mem:02d}.t12z.pgrb2a.0p50.f003", "gep{mem:02d}.t12z.pgrb2b.0p50.f003"],
        ),
    ],
)
def test_retrieve_data_aws_pull_data_systest(data_set, filefmt, filenames, tmp_path):
    cycle = "2025-05-05T12"
    args = [
        "--fileset",
        "anl",
        "--config",
        str(Path(f"{__file__}/../../../parm/data_locations.yml").resolve()),
        "--cycle",
        cycle,
        "--data-stores",
        "aws",
        "--data-type",
        data_set,
        "--fcst-hrs",
        "3",
        "--output-path",
        str(tmp_path),
        "--debug",
        "--filefmt",
        filefmt,
        "--members",
        "1",
        "2",
    ]
    retrieve_data.main(args)
    for filename in filenames:
        for mem in (1, 2):
            fn = filename.format(mem=mem)
            assert (tmp_path / f"mem{mem:03d}" / fn).is_file()


@mark.parametrize(
    ("data_set", "filename"),
    [
        ("GFS", "gfs.t00z.pgrb2.0p25.f{h:03d}"),
        ("HRRR", "hrrr.t00z.wrfprsf{h:02d}.grib2"),
        ("RAP", "rap.t00z.wrfnatf{h:02d}.grib2"),
    ],
)
def test_retrieve_data_hpss_pull_data_systest(data_set, filename, tmp_path):
    cycle = "2025-05-04T00"
    args = [
        "--fileset",
        "fcst",
        "--config",
        str(Path(f"{__file__}/../../../parm/data_locations.yml").resolve()),
        "--cycle",
        cycle,
        "--data-stores",
        "hpss",
        "--data-type",
        data_set,
        "--fcst-hrs",
        "6",
        "12",
        "3",
        "--output-path",
        str(tmp_path),
        "--debug",
        "--filefmt",
        "grib2",
    ]
    retrieve_data.main(args)
    fcst_hrs = (6, 9, 12)
    for fcst_hr in fcst_hrs:
        path = tmp_path / filename.format(h=fcst_hr)
        assert path.is_file()
