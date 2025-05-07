from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from pytest import mark

from scripts import common


def test_parse_args_valid():
    argv = [
        "-c",
        "config.yaml",
        "--cycle",
        "2025-01-01T00:00:00",
        "--lead",
        "6",
        "--key-path",
        "forecast.model",
    ]
    args = common.parse_args(argv)
    assert args.config_file == Path("config.yaml")
    assert args.cycle == datetime(2025, 1, 1, 0, 0, tzinfo=timezone.utc)
    assert args.lead == 6
    assert args.key_path == ["forecast", "model"]


@mark.parametrize("success", [True, False])
def test_check_success(success):
    rundir = Path("/some/directory")
    done_file = "runscript.done"
    with (
        patch("scripts.common.Path.is_file", return_value=success),
        patch("scripts.common.sys.exit") as mock_exit,
    ):
        common.check_success(rundir, done_file)
    if success:
        mock_exit.assert_not_called()
    else:
        mock_exit.assert_called_once_with(1)


def test_run_component(caplog):
    class FakeDriver:
        def __init__(self, config, cycle, key_path, leadtime):
            config = {"rundir": "/mock/rundir"}
            self.config = config
            self.cycle = cycle
            self.key_path = key_path
            self.leadtime = leadtime

        def run(self):
            pass

    config_file = Path("/some/config.yaml")
    cycle = datetime(2025, 1, 1, 12, tzinfo=timezone.utc)
    key_path = ["forecast"]
    lead = timedelta(hours=6)
    caplog.set_level("INFO")
    rundir = common.run_component(
        driver_class=FakeDriver,
        config_file=config_file,
        cycle=cycle,
        key_path=key_path,
        lead=lead,
    )
    assert rundir == Path("/mock/rundir")
    assert "Running FakeDriver in /mock/rundir" in caplog.text
