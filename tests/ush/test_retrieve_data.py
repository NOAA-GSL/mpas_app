import datetime as dt
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import Mock, patch

from pytest import fixture
from uwtools.api.config import get_yaml_config
from uwtools.api.logging import use_uwtools_logger
from uwtools.api.template import render

from ush import retrieve_data


@fixture
def data_locations():
    return get_yaml_config(Path(f"{__file__}/../../../parm/data_locations.yml").resolve())


def test_import():
    assert retrieve_data


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
        file_templates=[tmp_file],
        lead_times=lead_times,
        locations=[file_path],
        members=[0],
        outpath=output_path,
    )
    assert not success


def test_prepare_fs_copy_config_gfs_grib2_aws(data_locations, tmp_path):
    output_path = tmp_path / "output"
    output_path.mkdir()

    leads = (6, 12)
    cycle = dt.datetime.fromisoformat("2025-05-04T00").replace(tzinfo=dt.timezone.utc)
    lead_times = [dt.timedelta(hours=l) for l in leads]
    expected = {
        f"gfs.t{cycle.hour:02d}z.{level}f{lead:03d}.nc": f"https://noaa-gfs-bdp-pds.s3.amazonaws.com/gfs.{cycle.strftime('%Y%m%d')}/{cycle.hour:02d}/atmos/gfs.t{cycle.hour:02d}z.{level}f{lead:03d}.nc"
        for lead in leads
        for level in ("atm", "sfc")
    }
    config = retrieve_data.prepare_fs_copy_config(
        config=data_locations,
        cycle=cycle,
        file_templates=data_locations["GFS"]["file_names"]["fcst"]["netcdf"],
        lead_times=lead_times,
        location=data_locations["GFS"]["aws"]["locations"][0],
        members=[0],
    )
    print("CONFIG: ", config)
    print(expected)
    assert config == expected
