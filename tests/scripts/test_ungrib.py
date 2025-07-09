from pathlib import Path
from unittest.mock import patch

from scripts import ungrib


def test_file__missing(tmp_path):
    path = tmp_path / "file"
    assert not ungrib.file(path=path).ready


def test_file__present(tmp_path):
    path = tmp_path / "file"
    path.touch()
    assert ungrib.file(path=path).ready


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

        assert kwargs["env"] == {}
        assert kwargs["cwd"] == tmp_path
        assert kwargs["taskname"] == "regrid_input"
