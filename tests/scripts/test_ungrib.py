from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import call, patch

from pytest import fixture, mark
from uwtools.api.config import get_yaml_config

from scripts import ungrib


@fixture
def ungrib_config(tmp_path):
    return get_yaml_config(
        {
            "user": {"ics": {"external_model": "GFS"}},
            "ungrib_ics": {
                "ungrib": {
                    "rundir": str(tmp_path),
                    "execution": {"executable": "/path/to/ungrib.exe"},
                    "gribfiles": {
                        "interval_hours": 1,
                        "max_leadtime": 2,
                        "offset": 0,
                        "path": "/some/path",
                    },
                    "vtable": "/path/to/vtable",
                },
            },
        }
    )


def test_file__missing(tmp_path):
    path = tmp_path / "file"
    assert not ungrib.file(path=path).ready


def test_file__present(tmp_path):
    path = tmp_path / "file"
    path.touch()
    assert ungrib.file(path=path).ready


def test_link_to_regridded_grib(tmp_path):
    orig_file = tmp_path / "orig.grib2"
    orig_file.touch()
    infile = tmp_path / "GRIBFILE.AAA"
    infile.symlink_to(orig_file)
    merged_vectors_file = tmp_path / "orig.tmp2.grib2"
    with patch.object(ungrib, "merge_vector_fields", side_effect=merged_vectors_file.touch()):
        ungrib.link_to_regridded_grib(
            infile,
            tmp_path,
            {},
        )
        assert infile.resolve() == merged_vectors_file


def test_main(args):
    with (
        patch.object(ungrib, "parse_args", return_value=args) as parse_args,
        patch.object(ungrib, "run_ungrib") as run_ungrib,
    ):
        ungrib.main()
        parse_args.assert_called_once()
        run_ungrib.assert_called_once_with(
            config_file=args.config_file,
            cycle=args.cycle,
            key_path=args.key_path,
        )


def test_merge_vector_fields(tmp_path):
    wgrib_config = {
        "grid_vectors": "abc",
    }
    infile = tmp_path / "infile"
    infile.touch()
    regrid_outfile = tmp_path / "infile.tmp.grib2"
    regrid_outfile.touch()
    outfile = tmp_path / "outfile"
    with patch.object(ungrib, "run_shell_cmd") as run_shell_cmd:
        ungrib.merge_vector_fields(Path(infile), outfile, tmp_path, wgrib_config)
        run_shell_cmd.assert_called_once()
        args, kwargs = run_shell_cmd.call_args

        assert kwargs["cwd"] == tmp_path
        assert kwargs["taskname"] == "merge_vector_fields"


def test_regrid_input(tmp_path):
    fields_file = tmp_path / "fields"
    fields_file.write_text("foo:bar")
    wgrib_config = {
        "budget_fields": fields_file,
        "neighbor_fields": fields_file,
        "grid_vectors": "abc",
        "grid_specs": "xyz",
    }
    infile = tmp_path / "infile"
    infile.touch()
    with patch.object(ungrib, "run_shell_cmd") as run_shell_cmd:
        ungrib.regrid_input(Path(infile), tmp_path, wgrib_config)
        run_shell_cmd.assert_called_once()
        args, kwargs = run_shell_cmd.call_args

        assert "foo:bar ' -new_grid_interpolation neighbor" in kwargs["cmd"]
        assert kwargs["cwd"] == tmp_path
        assert kwargs["taskname"] == "regrid_input"


def test_regrid_winds(tmp_path):
    expected_calls = []
    for label in ("AAA", "AAB", "AAC"):
        grib_file = tmp_path / f"GRIBFILE.{label}"
        grib_file.touch()
        expected_calls.append(call(grib_file, tmp_path, {}))
    with patch.object(ungrib, "link_to_regridded_grib") as linker:
        ungrib.regrid_winds(tmp_path, {"wgrib2": {}})
        linker.assert_has_calls(expected_calls)


@mark.parametrize("outcome", ["pass", "fail"])
def test_run_ungrib_gfs(outcome, tmp_path, ungrib_config):
    config_file = tmp_path / "experiment.yaml"
    ungrib_config.dump(config_file)
    cycle = datetime(2025, 1, 1, 12, tzinfo=timezone.utc)
    side_effect = (tmp_path / "runscript.ungrib.done").touch() if outcome == "pass" else None
    with (
        patch.object(ungrib.Ungrib, "run", side_effect=side_effect) as run,
        patch("sys.exit") as sysexit,
    ):
        ungrib.run_ungrib(config_file, cycle, ["ungrib_ics"])
        run.assert_called_once()
        if outcome == "fail":
            sysexit.assert_called_once_with(1)


def test_run_ungrib_rrfs(tmp_path, ungrib_config):
    config_file = tmp_path / "experiment.yaml"
    ungrib_config.update_from({"user": {"ics": {"external_model": "RRFS"}}})
    ungrib_config.dump(config_file)
    cycle = datetime(2025, 1, 1, 12, tzinfo=timezone.utc)
    side_effect = (tmp_path / "runscript.ungrib.done").touch()
    with (
        patch.object(ungrib.Ungrib, "run", side_effect=side_effect) as run,
        patch.object(ungrib.Ungrib, "gribfiles") as gribfiles,
        patch.object(ungrib, "regrid_winds") as regrid_winds,
    ):
        ungrib.run_ungrib(config_file, cycle, ["ungrib_ics"])
        gribfiles.assert_called_once()
        regrid_winds.assert_called_once_with(str(tmp_path), ungrib_config["ungrib_ics"])
        run.assert_called_once()
