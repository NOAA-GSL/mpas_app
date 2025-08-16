from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import ANY, Mock, call, patch

import iotaa
from pytest import fixture, mark
from uwtools.api.config import get_yaml_config

from scripts import ungrib


@fixture
def ungrib_config(tmp_path):
    tmp_input = tmp_path / "input_data"
    tmp_input.mkdir()
    return get_yaml_config(
        {
            "user": {"ics": {"external_model": "GFS"}, "lbcs": {"external_model": "GFS"}},
            "ungrib_ics": {
                "ungrib": {
                    "rundir": str(tmp_path),
                    "execution": {"executable": "/path/to/ungrib.exe"},
                    "gribfiles": [str(tmp_input)],
                    "start": "2025-07-31T00:00:00",
                    "step": 6,
                    "stop": "2025-07-31T00:00:00",
                    "vtable": "/path/to/vtable",
                },
                "wgrib2": {},
            },
            "ungrib_lbcs": {
                "ungrib": {
                    "rundir": str(tmp_path),
                    "execution": {"executable": "/path/to/ungrib.exe"},
                    "gribfiles": [str(tmp_input)],
                    "start": "2025-07-31T00:00:00",
                    "step": 6,
                    "stop": "2025-07-31T00:00:00",
                    "vtable": "/path/to/vtable",
                },
                "wgrib2": {},
            },
        }
    )


@fixture
def ungrib_driver(ungrib_config):
    cycle = datetime(2025, 1, 1, 12, tzinfo=timezone.utc)
    return ungrib.Ungrib(config=ungrib_config, cycle=cycle, key_path=["ungrib_ics"])


@iotaa.external
def noop(*_args, **_kwargs):
    yield "No op"
    yield iotaa.asset(None, lambda: True)


@iotaa.external
def noop_not_ready(*_args, **_kwargs):
    yield "No op not ready"
    yield iotaa.asset(None, lambda: False)


def test_file__missing(tmp_path):
    path = tmp_path / "file"
    assert not ungrib.file(path=path).ready


def test_file__present(tmp_path):
    path = tmp_path / "file"
    path.touch()
    assert ungrib.file(path=path).ready


@mark.parametrize("wrap", [noop, noop_not_ready])
def test_main(args, wrap):
    with (
        patch.object(ungrib, "parse_args", return_value=args) as parse_args,
        patch.object(ungrib, "run_ungrib", return_value=wrap()) as run_ungrib,
        patch.object(ungrib.sys, "exit") as sysexit,
    ):
        ungrib.main()
        parse_args.assert_called_once()
        run_ungrib.assert_called_once_with(
            config_file=args.config_file,
            cycle=args.cycle,
            key_path=args.key_path,
        )
        if not run_ungrib.ready:
            assert sysexit.assert_called_once_with(1)


@mark.parametrize("success", [True, False])
def test_merge_vector_fields(success, tmp_path, ungrib_driver):
    wgrib_config = {
        "grid_vectors": "abc",
    }
    infile = tmp_path / "infile"
    regrid_outfile = tmp_path / "tmp.infile.grib2"
    outfile = tmp_path / "tmp2.infile.grib2"
    with (
        patch.object(ungrib, "run_shell_cmd", return_value=(success, "")) as run_shell_cmd,
        patch.object(ungrib, "regrid_input", wraps=noop, side_effect=regrid_outfile.touch()),
    ):
        ungrib.merge_vector_fields(ungrib_driver, infile, wgrib_config)
        run_shell_cmd.assert_called_once()
        args, kwargs = run_shell_cmd.call_args

        assert kwargs["cwd"] == tmp_path
        assert kwargs["taskname"] == f"wgrib2 merge vector fields {infile}"
        if success:
            assert infile.resolve() == outfile
        else:
            assert not outfile.is_file()


def test_regrid_input(ungrib_driver, tmp_path):
    fields_file = tmp_path / "fields"
    fields_file.write_text("foo:bar")
    wgrib_config = {
        "budget_fields": fields_file,
        "neighbor_fields": fields_file,
        "grid_vectors": "abc",
        "grid_specs": "xyz",
    }
    grib_file = tmp_path / "a.grib2"
    grib_file.touch()
    infile = tmp_path / "GRIBFILE.AAA"
    infile.symlink_to(grib_file)
    with (
        patch.object(ungrib, "run_shell_cmd") as run_shell_cmd,
        patch.object(ungrib.Ungrib, "gribfiles") as gribfiles,
    ):
        ungrib.regrid_input(ungrib_driver, infile, wgrib_config)
        gribfiles.assert_called_once()
        run_shell_cmd.assert_called_once()
        args, kwargs = run_shell_cmd.call_args

        assert "foo:bar ' -new_grid_interpolation neighbor" in kwargs["cmd"]
        assert kwargs["cwd"] == tmp_path
        assert kwargs["taskname"] == f"wgrib2 regrid {infile}"

        assert not infile.is_symlink()


def test_regrid_all(tmp_path, ungrib_driver):
    expected_calls = []
    for label in ("AAA", "AAB", "AAC", "AAD"):
        grib_file = tmp_path / f"GRIBFILE.{label}"
        expected_calls.append(call(ungrib_driver, grib_file, {"wgrib2": {}}))
    gribfiles = Mock()
    gribfiles.ref = [tmp_path / f"GRIBFILE.{label}" for label in ("AAA", "AAB", "AAC", "AAD")]
    with (
        patch.object(ungrib.Ungrib, "gribfiles", return_value=gribfiles),
        patch.object(ungrib, "merge_vector_fields") as wgrib_task,
    ):
        ungrib.regrid_all(ungrib_driver, {"wgrib2": {}})
        assert expected_calls == wgrib_task.call_args_list


@mark.parametrize("outcome", ["pass", "fail"])
def test_run_ungrib_gfs(outcome, tmp_path, ungrib_config):
    external_model = ungrib_config["user"]["ics"]["external_model"]
    orig_rundir = Path(ungrib_config["ungrib_ics"]["ungrib"]["rundir"])
    target_dir = orig_rundir.parent / external_model
    target_dir.mkdir(parents=True, exist_ok=True)
    (target_dir / "ICS.yaml").write_text(repr(get_yaml_config({"dst.grib2": "src.grib2"})))
    config_file = tmp_path / "experiment.yaml"
    ungrib_config.dump(config_file)
    cycle = datetime(2025, 1, 1, 12, tzinfo=timezone.utc)
    side_effect = (tmp_path / "runscript.ungrib.done").touch() if outcome == "pass" else None
    with patch.object(ungrib.Ungrib, "run", side_effect=side_effect) as run:
        task_state = ungrib.run_ungrib(config_file, cycle, ["ungrib_ics"])
        if outcome == "pass":
            assert (tmp_path / "runscript.ungrib.done").exists()
        else:
            run.assert_called_once()
            assert not task_state.ready


def test_run_ungrib_rrfs(tmp_path, ungrib_config):
    ungrib_config.update_from({"user": {"ics": {"external_model": "RRFS"}}})
    external_model = ungrib_config["user"]["ics"]["external_model"]
    orig_rundir = Path(ungrib_config["ungrib_ics"]["ungrib"]["rundir"])
    target_dir = orig_rundir.parent / external_model
    target_dir.mkdir(parents=True, exist_ok=True)
    (target_dir / "ICS.yaml").write_text(repr(get_yaml_config({"dst.grib2": "src.grib2"})))
    config_file = tmp_path / "experiment.yaml"
    ungrib_config.update_from({"user": {"ics": {"external_model": "RRFS"}}})
    ungrib_config.dump(config_file)
    cycle = datetime(2025, 1, 1, 12, tzinfo=timezone.utc)

    with (
        patch.object(ungrib.Ungrib, "run") as run,
        patch.object(ungrib, "regrid_all", wraps=noop) as regrid_all,
    ):
        ungrib.run_ungrib(config_file, cycle, ["ungrib_ics"])
        regrid_all.assert_called_once_with(ANY, ungrib_config["ungrib_ics"]["wgrib2"])
        run.assert_called_once()


def test_run_ungrib_rrfs_lbcs(tmp_path, ungrib_config):
    ungrib_config.update_from({"user": {"lbcs": {"external_model": "RRFS"}}})
    external_model = ungrib_config["user"]["lbcs"]["external_model"]
    orig_rundir = Path(ungrib_config["ungrib_lbcs"]["ungrib"]["rundir"])
    target_dir = orig_rundir.parent / external_model
    target_dir.mkdir(parents=True, exist_ok=True)
    (target_dir / "ICS.yaml").write_text(repr(get_yaml_config({"dst_a.grib2": "src.grib2"})))
    (target_dir / "LBCS.yaml").write_text(repr(get_yaml_config({"dst_b.grib2": "src.grib2"})))
    config_file = tmp_path / "experiment.yaml"
    ungrib_config.dump(config_file)
    cycle = datetime(2025, 1, 1, 12, tzinfo=timezone.utc)

    with (
        patch.object(ungrib.Ungrib, "run") as run,
        patch.object(ungrib, "regrid_all", wraps=noop) as regrid_all,
    ):
        ungrib.run_ungrib(config_file, cycle, ["ungrib_lbcs"])
        regrid_all.assert_called_once_with(ANY, ungrib_config["ungrib_lbcs"]["wgrib2"])
        run.assert_called_once()
