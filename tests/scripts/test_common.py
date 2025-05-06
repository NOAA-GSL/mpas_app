from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import Mock, patch

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


def test_check_success():
    rundir = Path("/some/directory")
    done_file = "runscript.done"
    with (
        patch("scripts.common.Path.is_file", return_value=True),
        patch("scripts.common.sys.exit") as mock_exit,
    ):
        common.check_success(rundir, done_file)
        mock_exit.assert_not_called()


def test_check_success_failure():
    rundir = Path("/some/directory")
    done_file = "runscript.done"
    with (
        patch("scripts.common.Path.is_file", return_value=False),
        patch("scripts.common.sys.exit") as mock_exit,
    ):
        common.check_success(rundir, done_file)
        mock_exit.assert_called_once_with(1)


def test_run_component():
    mock_driver_class = Mock()
    mock_driver_class.__name__ = "MockDriverClass"
    mock_driver_instance = Mock()
    mock_driver_class.return_value = mock_driver_instance
    mock_driver_instance.config = {"rundir": "/mock/rundir"}
    mock_driver_instance.run = Mock()
    config_file = Path("/some/config.yaml")
    cycle = datetime(2025, 1, 1, 12, tzinfo=timezone.utc)
    key_path = ["forecast"]
    lead = timedelta(hours=6)
    with patch("scripts.common.logging.info") as mock_logging_info:
        rundir = common.run_component(
            driver_class=mock_driver_class,
            config_file=config_file,
            cycle=cycle,
            key_path=key_path,
            lead=lead,
        )
        mock_driver_class.assert_called_once_with(
            config=str(config_file), cycle=cycle, key_path=key_path, leadtime=lead
        )
        mock_driver_instance.run.assert_called_once()
        assert rundir == Path("/mock/rundir")
        mock_logging_info.assert_called_once_with(
            "Running %s in %s", mock_driver_class.__name__, Path("/mock/rundir")
        )
