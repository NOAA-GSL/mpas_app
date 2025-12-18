"""
Tracker driver tests.
"""

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import call, patch

from iotaa import asset, external
from pytest import fixture

from drivers import tracker


@fixture
def config(tmp_path):
    return {
        "gfdltracker": {
            "basins": "L",
            "execution": {
                "executable": "tracker.exe",
                "batchargs": {"walltime": "01:00:00"},
                "envcmds": ["foo", "bar"],
            },
            "input_files": {
                "endhour": 12,
                "filefreq": 6,
                "filepath": str(
                    tmp_path / "input" / "gribf{{ '%02d' % (leadtime.total_seconds() / 3600) }}"
                ),
            },
            "namelist": {
                "update_values": {
                    "trackerinfo": {
                        "trkrinfo": {
                            "eastbd": 3313,
                            "westbd": 20,
                            "northbd": 2646,
                            "southbd": 20,
                        },
                    },
                },
            },
            "rundir": str(tmp_path / "tracker"),
            "tcvitals": "/path/to/tcvitals/syntdat_tcvitals.2025",
        }
    }


@fixture
def cycle(utc):
    return utc(2024, 2, 1, 18)


@fixture
def driverobj(config, cycle):
    schema_file = Path(__name__).parent.parent.parent.absolute() / "drivers" / "tracker.jsonschema"
    return tracker.GFDLTracker(config=config, cycle=cycle, batch=True, schema_file=schema_file)


@fixture
def outpath(driverobj):
    return lambda fn: driverobj.rundir / fn


@fixture
def ready_task():
    @external
    def ready(*_args, **_kwargs):
        yield "ready"
        yield asset(None, lambda: True)

    return ready


@fixture
def utc():
    def utc(*args, **kwargs) -> datetime:
        # See https://github.com/python/mypy/issues/6799
        tz = timezone.utc
        dt = datetime(*args, **kwargs, tzinfo=tz) if args or kwargs else datetime.now(tz=tz)  # type: ignore[misc]
        return dt.replace(tzinfo=None)

    return utc


def test_tracker_input_fcst_minutes(driverobj, ready_task):
    with (
        patch.object(driverobj, "input_files", new=ready_task),
        patch.object(driverobj, "input_index_files", new=ready_task),
    ):
        driverobj.input_fcst_minutes()
        path = driverobj.rundir / "fort.15"
        assert path.is_file()
        contents = path.read_text().strip("\n").split("\n")
        assert contents == ["   1     0", "   2   360", "   3   720"]


def test_tracker_input_files(driverobj, tmp_path):
    infiles = [Path(fp) for fp in driverobj._input_file_map().values()]
    for fp in infiles:
        fp.parent.mkdir(parents=True, exist_ok=True)
        fp.touch()
    driverobj.input_files()
    expected_links = [f"mpas.trak.all.2024020118.f{fmin:05d}" for fmin in (0, 360, 720)]
    for infile, outlink in zip(infiles, expected_links):
        expected = tmp_path / "tracker" / outlink
        assert expected.is_symlink()
        assert expected.resolve() == infile


def test_tracker_input_index_files(driverobj, ready_task):
    input_files = driverobj.input_files().ref
    with (
        patch.object(driverobj, "input_files", new=ready_task),
        patch.object(tracker, "run_shell_cmd") as run,
    ):
        driverobj.input_index_files()
    expected_calls = [
        call(
            cmd=f"foo && bar && grb2index {infile} {infile}.ix",
            cwd=driverobj.rundir,
            log_output=True,
        )
        for infile in input_files
    ]
    assert run.call_args_list == expected_calls


def test_tracker_driver_name(driverobj):
    assert driverobj.driver_name() == tracker.GFDLTracker.driver_name() == "gfdltracker"
