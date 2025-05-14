from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import Mock, patch

from pytest import fixture, mark, raises

from scripts import common


@fixture
def fake_driver():
    class FakeDriver:
        def __init__(self, config, cycle, key_path, leadtime=None):
            config = {"rundir": "/mock/rundir"}
            self.config = config
            self.cycle = cycle
            self.key_path = key_path
            self.leadtime = leadtime

        def run(self):
            pass

    return FakeDriver


def test_parse_args():
    argv = [
        "-c",
        "config.yaml",
        "--cycle",
        "2025-01-01T00:00:00",
        "--leadtime",
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
    with raises(SystemExit):
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
    with raises(SystemExit):
        common.parse_args(argv, lead_required=True)


@mark.parametrize("leadtime", [None, timedelta(hours=6)])
def test_run_component(caplog, fake_driver, leadtime, mock_args):
    caplog.set_level("INFO")
    driver = fake_driver
    with (
        patch.object(driver, "run", return_value=Mock(ready=True)),
        patch("scripts.common.use_uwtools_logger"),
    ):
        common.run_component(
            driver_class=driver,
            config_file=mock_args.config_file,
            cycle=mock_args.cycle,
            key_path=mock_args.key_path,
            leadtime=leadtime,
        )
    assert "Running FakeDriver in /mock/rundir" in caplog.text


def test_run_component_failure(caplog, fake_driver, mock_args):
    caplog.set_level("ERROR")
    driver = fake_driver
    with (
        patch.object(driver, "run", return_value=Mock(ready=False, refs=["/mock/rundir/file"])),
        patch("scripts.common.use_uwtools_logger"),
        patch("sys.exit") as mock_exit,
    ):
        common.run_component(
            driver_class=driver,
            config_file=mock_args.config_file,
            cycle=mock_args.cycle,
            key_path=mock_args.key_path,
            leadtime=None,
        )
    assert "Error occurred. Expected file /mock/rundir/file not found." in caplog.text
    mock_exit.assert_called_once_with(1)
