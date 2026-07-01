"""
Tracker driver tests.
"""

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import call, patch

from iotaa import Asset, external
from pytest import fixture

from drivers import tracker


@fixture
def config(tmp_path):
    return {
        "gfdltracker": {
            "basins": "LWE",
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
                "base_file": str(tmp_path / "input" / "foo.nml"),
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
            "tcvitals": str(
                Path(__name__).parent.resolve() / "tests" / "data" / "syndat_tcvitals.2025"
            ),
        }
    }


@fixture
def cycle(utc):
    return utc(2025, 10, 22, 18)


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
        yield Asset(None, lambda: True)

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
    expected_links = [f"mpas.trak.all.2025102218.f{fmin:05d}" for fmin in (0, 360, 720)]
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


def test_tracker_input_vitals(driverobj):
    # Expect two storms in the dataset at this cycle
    expected_fn = driverobj.rundir / "allvit"
    assert not expected_fn.is_file()
    driverobj.input_vitals()
    assert expected_fn.is_file()
    expected_storms = [
        "JTWC 30W FENGSHEN",
        "NHC  13L MELISSA",
    ]
    contents = expected_fn.read_text().strip("\n").split("\n")
    assert len(contents) == 2
    for line, exp in zip(contents, expected_storms):
        assert line.startswith(exp)


def test_tracker_input_vitals_other_names(driverobj):
    paths = [driverobj.rundir / p for p in ("allvit", "tcvit_rsmc_storms.txt", "fort.12")]
    for path in paths:
        assert not path.is_file()
    task = driverobj.input_vitals_other_names()
    assert task.ready
    assert paths[0].is_file()
    assert not paths[0].is_symlink()
    for path in paths[1:]:
        assert path.is_symlink()
        assert path.resolve() == paths[0]


def test_tracker_namelist_file(driverobj, tmp_path):
    base_nml = tmp_path / "input" / "foo.nml"
    base_nml.parent.mkdir()
    base_nml.write_text("&trackerinfo \n /")
    expected = """&trackerinfo
    trkrinfo%eastbd = 3313
    trkrinfo%northbd = 2646
    trkrinfo%southbd = 20
    trkrinfo%westbd = 20
/

&datein
    inp%bcc = 20
    inp%bdd = 22
    inp%bhh = 18
    inp%bmm = 10
    inp%byy = 25
/

&atcfinfo
    atcfymdh = 2025102218
/
"""
    driverobj.namelist_file()
    nml = driverobj.rundir / "namelist.gettrk"
    contents = nml.read_text()
    assert contents == expected


def test_tracker_provisioned_rundir(driverobj, ready_task):
    with patch.multiple(
        driverobj,
        input_fcst_minutes=ready_task,
        input_files=ready_task,
        input_index_files=ready_task,
        input_vitals=ready_task,
        input_vitals_other_names=ready_task,
        namelist_file=ready_task,
        runscript=ready_task,
    ):
        assert driverobj.provisioned_rundir().ready


def test_tracker_driver_name(driverobj):
    assert driverobj.driver_name() == tracker.GFDLTracker.driver_name() == "gfdltracker"


def test_tracker__input_file_map(driverobj, tmp_path):
    infilepath = tmp_path / "input"
    expected = {
        0: str(infilepath / "gribf00"),
        6: str(infilepath / "gribf06"),
        12: str(infilepath / "gribf12"),
    }
    filemap = driverobj._input_file_map()
    assert filemap == expected


def test_tracker__validate(driverobj):
    with (
        patch.object(tracker.Assets, "_validate") as asset_valid,
        patch.object(tracker, "validate_internal") as internal_valid,
        patch.object(tracker, "TrackerNamelist") as namelist_valid,
    ):
        driverobj._validate()
    asset_valid.assert_called_once()
    internal_valid.assert_called_once()
    namelist_valid.assert_called_once()
