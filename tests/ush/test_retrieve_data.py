import datetime as dt
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import Mock, call, patch

from pytest import fixture, mark, raises
from uwtools.api.config import get_yaml_config
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


def test_get_file_names_no_file_fmt():
    files = {"anl": ["file1.txt", "file2.txt"]}
    result = retrieve_data.get_file_names(file_name_config=files, file_fmt="foo", file_set="anl")
    assert result == files["anl"]


def test_get_file_names_file_fmt():
    files = {"anl": {"grib2": ["file1.txt", "file2.txt"]}}
    result = retrieve_data.get_file_names(file_name_config=files, file_fmt="grib2", file_set="anl")
    assert result == files["anl"]["grib2"]


def test_try_data_store_disk_success(data_locations, tmp_path):
    file_path = tmp_path / "{{ cycle.strftime('%Y%m%d%H') }}"
    output_path = tmp_path / "output"
    output_path.mkdir()
    tmp_file = "tmp.f{{ fcst_hr }}"
    existing_file_template = file_path / tmp_file
    cycle = dt.datetime.now(tz=dt.timezone.utc)
    lead_times = [dt.timedelta(hours=6), dt.timedelta(hours=12)]

    new_files = []
    for lead_time in lead_times:
        input_stream = StringIO(str(existing_file_template))
        sys.stdin = input_stream
        values = {
            "cycle": cycle,
            "fcst_hr": lead_time.seconds // 3600,
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


def test_try_data_store_disk_fail(tmp_path):
    file_path = tmp_path / "{{ cycle.strftime('%Y%m%d%H') }}"
    output_path = tmp_path / "output"
    output_path.mkdir()
    tmp_file = "tmp.f{{ fcst_hr }}"
    existing_file_template = file_path / tmp_file
    cycle = dt.datetime.now(tz=dt.timezone.utc)
    lead_times = [dt.timedelta(hours=6), dt.timedelta(hours=12)]

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


def test_try_data_store_hpss(data_locations, tmp_path):
    gfs_config = data_locations["GFS"]
    cycle = dt.datetime.now(tz=dt.timezone.utc)
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


def count_iterator(iterator):
    count = 0
    for _ in iterator:
        count += 1
    return count


def test_possible_hpss_configs(data_locations):
    leads = (6, 12)
    cycle = dt.datetime.fromisoformat("2025-05-04T00").replace(tzinfo=dt.timezone.utc)
    lead_times = [dt.timedelta(hours=l) for l in leads]

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
    cycle = dt.datetime.fromisoformat("2025-05-04T00").replace(tzinfo=dt.timezone.utc)
    lead_times = [dt.timedelta(hours=l) for l in leads]
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
    remove_args = ("data_stores", "data_type", "file_fmt", "file_set", "ics_or_lbcs", "inpath")

    cycle = dt.datetime.fromisoformat("2025-05-04T00").replace(tzinfo=dt.timezone.utc)
    args = {
        "config": {data_set: data_locations[data_set]},
        "cycle": cycle,
        "data_stores": data_stores,
        "data_type": data_set,
        "file_set": "fcst",
        "outpath": tmp_path / "output",
        "file_fmt": "netcdf",
        "file_templates": ["a.f{{ '%3d' % fcst_hr }}.grib"],
        "lead_times": [6],
        "members": [None],
        "ics_or_lbcs": "lbcs",
        "inpath": tmp_path / "input",
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
