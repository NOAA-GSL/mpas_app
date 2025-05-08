from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock, patch

from scripts import mpas


def test_main():
    mock_args = Mock()
    mock_args.config_file = Path("/some/config.yaml")
    mock_args.cycle = datetime(2025, 1, 1, 12, tzinfo=timezone.utc)
    mock_args.key_path = ["forecast"]
    with (
        patch.object(mpas, "parse_args", return_value=mock_args) as mock_parse_args,
        patch.object(
            mpas, "run_component", return_value=Path("/some/rundir")
        ) as mock_run_component,
        patch.object(mpas, "check_success") as mock_check_success,
    ):
        mpas.main()
        mock_parse_args.assert_called_once()
        mock_run_component.assert_called_once_with(
            driver_class=mpas.MPAS,
            config_file=mock_args.config_file,
            cycle=mock_args.cycle,
            key_path=mock_args.key_path,
        )
        mock_check_success.assert_called_once_with(Path("/some/rundir"), "mpas")
