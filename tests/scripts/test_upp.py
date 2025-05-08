from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock, patch

from scripts import upp


def test_main():
    mock_args = Mock()
    mock_args.config_file = Path("/some/config.yaml")
    mock_args.cycle = datetime(2025, 1, 1, 12, tzinfo=timezone.utc)
    mock_args.lead = 6
    mock_args.key_path = ["forecast"]
    with (
        patch.object(upp, "parse_args", return_value=mock_args) as mock_parse_args,
        patch.object(upp, "run_component", return_value=Path("/some/rundir")) as mock_run_component,
        patch.object(upp, "check_success") as mock_check_success,
    ):
        upp.main()
        mock_parse_args.assert_called_once()
        mock_run_component.assert_called_once_with(
            driver_class=upp.UPP,
            config_file=mock_args.config_file,
            cycle=mock_args.cycle,
            lead=mock_args.lead,
            key_path=mock_args.key_path,
        )
        mock_check_success.assert_called_once_with(Path("/some/rundir"), "upp")
