import argparse
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from io import StringIO
from pathlib import Path
from unittest.mock import Mock, call, patch

from pytest import fixture, mark, raises
from uwtools.api.config import YAMLConfig, get_yaml_config
from uwtools.api.logging import use_uwtools_logger
from uwtools.api.template import render

from ush import retrieve_data


@fixture
def data_locations():
    return get_yaml_config(Path(f"{__file__}/../../../parm/data_locations.yml").resolve())


def test_import():
    assert retrieve_data


def test__abort(capsys):
    msg = "exit from _abort"
    with raises(SystemExit) as e:
        retrieve_data._abort(msg)
    assert e.type == SystemExit
    assert e.value.code == 1
    assert msg in capsys.readouterr().err


@mark.parametrize("inargs,expected", [([0], [0]), ([2, 5], [2, 3, 4, 5]), ([0, 12, 6], [0, 6, 12])])
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
    assert f"Specify leadtime as hours[:minutes[:seconds]]" in capsys.readouterr().err


def test_get_file_names_file_fmt():
    files = {"anl": {"grib2": ["file1.txt", "file2.txt"]}}
    result = retrieve_data.get_file_names(file_name_config=files, file_fmt="grib2", file_set="anl")
    assert result == files["anl"]["grib2"]


def test_get_file_names_no_file_fmt():
    files = {"anl": ["file1.txt", "file2.txt"]}
    result = retrieve_data.get_file_names(file_name_config=files, file_fmt="foo", file_set="anl")
    assert result == files["anl"]


def test_main(tmp_path):
    config = Path(f"{__file__}/../../../parm/data_locations.yml").resolve()
    config = tmp_path / "data_locations.yml"
    config.write_text("foo: bar")
    cycle = "2025-05-04T00"
    cycle_dt = datetime.fromisoformat(cycle).replace(tzinfo=timezone.utc)
    args = [
        "--file-set",
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
        "--file-fmt",
        "grib2",
    ]
    with patch.object(retrieve_data, "retrieve_data") as retrieve:
        retrieve_data.main(args)
    actual = retrieve.call_args.kwargs
    expected_args = dict(
        config=get_yaml_config(str(config)),
        cycle=cycle_dt,
        data_stores=["aws"],
        data_type="GFS",
        file_set="fcst",
        file_fmt="grib2",
        lead_times=[timedelta(hours=i) for i in (6, 9, 12)],
        file_templates=[],
        inpath=None,
        members=[-999],
        outpath=tmp_path,
        summary_file=None,
        symlink=False,
    )
    from pprint import pprint

    print("ACTUAL")
    # pprint(actual)
    print("EXPECTED")
    # pprint(expected_args)
    print(expected_args["config"].compare_config(actual["config"].data))
    # expected_args["config"].dump(Path("./expected_args.yaml"))
    # actual["config"].dump(Path("actual_args.yaml"))
    # actual["config"].compare_config(expected_args["config"].__dict__)
    retrieve.assert_called_with(**expected_args)


def test_try_data_store_disk_fail(tmp_path):
    file_path = tmp_path / "{{ cycle.strftime('%Y%m%d%H') }}"
    output_path = tmp_path / "output"
    output_path.mkdir()
    tmp_file = "tmp.f{{ fcst_hr }}"
    existing_file_template = file_path / tmp_file
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
        input_stream = StringIO(str(existing_file_template))
        sys.stdin = input_stream
        values = {
            "cycle": cycle,
            "fcst_hr": int(lead_time.total_seconds() // 3600),
        }
        new_file = Path(render(values_src=values, stdin_ok=True))
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
        members=[0],
        outpath=output_path,
    )
    assert all([(output_path / f.name).is_file() for f in new_files])
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
            file_templates=retrieve_data.get_file_names(gfs_config["file_names"], "grib2", "anl"),
            lead_times=[0],
            locations=gfs_config["hpss"]["locations"],
            members=[None],
            outpath=tmp_path / "output",
            archive_config=gfs_config["hpss"],
            archive_names=retrieve_data.get_file_names(
                gfs_config["hpss"]["archive_file_names"], "grib2", "anl"
            ),
        )
    possible_hpss_configs.assert_called_once_with(
        archive_locations=gfs_config["hpss"],
        archive_names=gfs_config["hpss"]["archive_file_names"]["anl"]["grib2"],
        config={"GFS": gfs_config},
        cycle=cycle,
        file_templates=["gfs.t{{hh}}z.pgrb2.0p25.f000"],
        lead_times=[0],
        members=[None],
    )


def test_parse_args(capsys, tmp_path):
    cycle = "2025-05-04T00"
    sysargs = [
        "--file-set",
        "fcst",
        "--config",
        str(Path(f"{__file__}/../../../parm/data_locations.yml").resolve()),
        "--cycle",
        cycle,
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
        "--file-fmt",
        "grib2",
    ]
    with patch(
        "ush.retrieve_data.subprocess.run",
        side_effect=[subprocess.CompletedProcess(args="/usr/bin/which hsi", returncode=0)],
    ):
        args = retrieve_data.parse_args(sysargs)
    assert args.file_set in retrieve_data.FILE_SETS
    assert isinstance(args.config, YAMLConfig)
    assert isinstance(args.cycle, datetime)
    assert isinstance(args.data_stores, list)
    assert all([ds in ["hpss", "nomads", "aws", "disk"] for ds in args.data_stores])
    assert args.data_type is not None
    assert args.fcst_hrs == [timedelta(hours=h) for h in (6, 9, 12)]
    assert args.output_path.is_absolute()
    assert not args.symlink
    assert args.debug
    assert args.file_templates == []
    assert args.file_fmt in ("grib2", "nemsio", "netcdf", "prepbufr", "tcvitals")
    assert args.input_file_path == tmp_path / "input"
    assert args.members == [-999]
    assert args.summary_file is None

    with patch(
        "ush.retrieve_data.subprocess.run",
        side_effect=subprocess.CalledProcessError(cmd="foo", returncode=1),
    ):
        with raises(SystemExit) as e:
            args = retrieve_data.parse_args(sysargs)

    sysargs.remove("--input-file-path")
    sysargs.remove(str(tmp_path / "input"))
    with raises(argparse.ArgumentTypeError):
        args = retrieve_data.parse_args(sysargs)


def count_iterator(iterator):
    count = 0
    for _ in iterator:
        count += 1
    return count


def test_possible_hpss_configs(data_locations):
    leads = (6, 12)
    cycle = datetime.fromisoformat("2025-05-04T00").replace(tzinfo=timezone.utc)
    lead_times = [timedelta(hours=l) for l in leads]

    expected1 = {
        "gfs.t00z.pgrb2.0p25.f000": "htar:///NCEPPROD/hpssprod/runhistory/rh2025/202505/20250504/gpfs_dell1_nco_ops_com_gfs_prod_gfs.20250504_00.gfs_pgrb2.tar?./gfs.20250504/00/gfs.t00z.pgrb2.0p25.f000"
    }

    expected2 = {
        "gfs.t00z.pgrb2.0p25.f000": "htar:///NCEPPROD/hpssprod/runhistory/rh2025/202505/20250504/com_gfs_prod_gfs.20250504_00.gfs_pgrb2.tar?./gfs.20250504/00/gfs.t00z.pgrb2.0p25.f000"
    }

    gfs_hpss = data_locations["GFS"]["hpss"]
    config = retrieve_data.possible_hpss_configs(
        archive_locations=gfs_hpss,
        archive_names=gfs_hpss["archive_file_names"]["anl"]["grib2"],
        config=data_locations,
        cycle=cycle,
        file_templates=data_locations["GFS"]["file_names"]["anl"]["grib2"],
        lead_times=lead_times,
        members=[0],
    )

    assert config.__next__() == expected1
    assert config.__next__() == expected2
    assert count_iterator(config) == 6  # already used first 2 of 8


def test_prepare_fs_copy_config_gfs_grib2_aws(data_locations):
    leads = (6, 12)
    cycle = datetime.fromisoformat("2025-05-04T00").replace(tzinfo=timezone.utc)
    lead_times = [timedelta(hours=l) for l in leads]
    expected = {
        f"gfs.t{cycle.hour:02d}z.{level}f{lead:03d}.nc": f"https://noaa-gfs-bdp-pds.s3.amazonaws.com/gfs.{cycle.strftime('%Y%m%d')}/{cycle.hour:02d}/atmos/gfs.t{cycle.hour:02d}z.{level}f{lead:03d}.nc"
        for lead in leads
        for level in ("atm", "sfc")
    }
    configs = retrieve_data.prepare_fs_copy_config(
        config=data_locations,
        cycle=cycle,
        file_templates=data_locations["GFS"]["file_names"]["fcst"]["netcdf"],
        lead_times=lead_times,
        locations=data_locations["GFS"]["aws"]["locations"],
        members=[0],
    )
    assert configs.__next__() == expected


@mark.parametrize("data_set", ["RAP", "GFS"])
def test_retrieve_data(data_locations, data_set, tmp_path):
    data_stores = ["disk", "aws", "hpss"]
    remove_args = ("data_stores", "data_type", "file_fmt", "file_set", "inpath", "summary_file")

    cycle = datetime.fromisoformat("2025-05-04T00").replace(tzinfo=timezone.utc)
    args = {
        "config": get_yaml_config({data_set: data_locations[data_set]}),
        "cycle": cycle,
        "data_stores": data_stores,
        "data_type": data_set,
        "file_set": "fcst",
        "outpath": tmp_path / "output",
        "file_fmt": "netcdf",
        "file_templates": ["a.f{{ '%3d' % fcst_hr }}.grib"],
        "lead_times": [6],
        "members": [None],
        "inpath": tmp_path / "input",
        "symlink": False,
        "summary_file": tmp_path / "summary.yaml",
    }
    with patch.object(retrieve_data, "try_data_store", return_value=(False, {})) as try_data_store:
        retrieved = retrieve_data.retrieve_data(**args)
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
            "file_templates": retrieve_data.get_file_names(
                data_locations[data_set]["file_names"], args["file_fmt"], "fcst"
            ),
            "locations": data_locations[data_set]["aws"]["locations"],
            "archive_config": None,
            "archive_names": None,
        }
        aws_calls.update(data_store_args)
        for key in remove_args:
            aws_calls.pop(key)

        hpss_calls = args.copy()
        archive_names = data_locations[data_set]["hpss"]["archive_file_names"]
        if isinstance(archive_names, dict):
            archive_names = data_locations[data_set]["hpss"]["archive_file_names"]["fcst"]["netcdf"]
        data_store_args = {
            "data_store": "hpss",
            "file_templates": retrieve_data.get_file_names(
                data_locations[data_set]["file_names"], args["file_fmt"], "fcst"
            ),
            "locations": data_locations[data_set]["hpss"]["locations"],
            "archive_config": data_locations[data_set]["hpss"],
            "archive_names": archive_names,
        }
        hpss_calls.update(data_store_args)
        for key in remove_args:
            hpss_calls.pop(key)

        from pprint import pprint

        print("CALLS")
        pprint(try_data_store.mock_calls[2].kwargs)
        print("expected")
        pprint(hpss_calls)
        (
            try_data_store.assert_has_calls(
                [call(**disk_calls), call(**aws_calls), call(**hpss_calls)]
            ),
        )


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
        "file_set": "anl",
        "outpath": tmp_path / "output",
        "file_fmt": "wgrib2",
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

    with patch.object(
        retrieve_data, "try_data_store", return_value=(True, summary)
    ) as try_data_store:
        retrieved = retrieve_data.retrieve_data(**args)

    assert retrieved is True
    assert summary_file.is_file()
    assert summary_file.read_text().strip() == get_yaml_config(summary).__repr__()


# Tests that pull data


def test_retrieve_data_hpss_pull_data_systest(tmp_path):
    cycle = "2025-05-04T00"
    args = [
        "--file-set",
        "fcst",
        "--config",
        str(Path(f"{__file__}/../../../parm/data_locations.yml").resolve()),
        "--cycle",
        cycle,
        "--data-stores",
        "hpss",
        "--data-type",
        "GFS",
        "--fcst-hrs",
        "6",
        "12",
        "3",
        "--output-path",
        str(tmp_path),
        "--debug",
        "--file-fmt",
        "grib2",
    ]
    retrieve_data.main(args)
    fcst_hrs = (6, 9, 12)
    for fcst_hr in fcst_hrs:
        path = tmp_path / f"gfs.t00z.pgrb2.0p25.f{fcst_hr:03d}"
        assert path.is_file()


@mark.parametrize(
    "data_set,file_fmt,filenames",
    [
        ("GDAS", "netcdf", ["gdas.t12z.sfcf003.nc", "gdas.t12z.atmf003.nc"]),
        ("GEFS", "grib2", ["gep001.t12z.pgrb2a.0p50.f003", "gep001.t12z.pgrb2b.0p50.f003"]),
    ],
)
def test_retrieve_data_aws_pull_data_systest(data_set, file_fmt, filenames, tmp_path):
    cycle = "2025-05-05T12"
    args = [
        "--file-set",
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
        str(tmp_path / "mem{{mem}}"),
        "--debug",
        "--file-fmt",
        file_fmt,
        "--members",
        "1",
    ]
    retrieve_data.main(args)
    for filename in filenames:
        assert (tmp_path / "mem1" / filename).is_file()
