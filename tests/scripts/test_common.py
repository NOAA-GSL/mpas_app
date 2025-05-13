from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts import common


def test_parse_args():
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
    assert args.leadtime == timedelta(seconds=21600)
    assert args.key_path == ["forecast", "model"]


def test_parse_args_invalid_cycle():
    argv = [
        "-c",
        "config.yaml",
        "--cycle",
        "01-01-2025 00:00",
        "--key-path",
        "forecast.model",
    ]
    with pytest.raises(SystemExit):
        common.parse_args(argv)


def test_parse_args_missing_leadtime():
    argv = [
        "-c",
        "config.yaml",
        "--cycle",
        "2025-01-01T00:00:00",
        "--key-path",
        "forecast.model",
    ]
    with pytest.raises(SystemExit):
        common.parse_args(argv, lead_required=True)


@pytest.mark.parametrize("success", [True, False])
def test_check_success(success):
    rundir = Path("/some/directory")
    with (
        patch("scripts.common.Path.is_file", return_value=success),
        patch("scripts.common.sys.exit") as mock_exit,
    ):
        common.check_success(rundir, "driver_name")
    if success:
        mock_exit.assert_not_called()
    else:
        mock_exit.assert_called_once_with(1)


def test_run_component(caplog):
    class FakeDriver:
        def __init__(self, config, cycle, key_path):
            config = {"rundir": "/mock/rundir"}
            self.config = config
            self.cycle = cycle
            self.key_path = key_path

        def run(self):
            pass

    config_file = Path("/some/config.yaml")
    cycle = datetime(2025, 1, 1, 12, tzinfo=timezone.utc)
    key_path = ["forecast"]
    caplog.set_level("INFO")
    rundir = common.run_component(
        driver_class=FakeDriver,
        config_file=config_file,
        cycle=cycle,
        key_path=key_path,
    )
    assert rundir == Path("/mock/rundir")
    assert "Running FakeDriver in /mock/rundir" in caplog.text


def test_run_component_with_leadtime(caplog):
    class FakeDriver:
        def __init__(self, config, cycle, key_path, leadtime=None):
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
    leadtime = timedelta(hours=6)
    caplog.set_level("INFO")
    rundir = common.run_component(
        driver_class=FakeDriver,
        config_file=config_file,
        cycle=cycle,
        key_path=key_path,
        leadtime=leadtime,
    )
    assert rundir == Path("/mock/rundir")
    assert "Running FakeDriver in /mock/rundir" in caplog.text
