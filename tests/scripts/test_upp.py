from pathlib import Path
from unittest.mock import patch

import pytest

from scripts import upp


def test_main(args):
    with (
        patch.object(upp, "parse_args", return_value=args) as parse_args,
        patch.object(upp, "run_component", return_value=Path("/some/rundir")) as run_component,
    ):
        upp.main()
        parse_args.assert_called_once()
        run_component.assert_called_once_with(
            driver_class=upp.UPP,
            config_file=args.config_file,
            cycle=args.cycle,
            leadtime=args.leadtime,
            key_path=args.key_path,
        )


def test_main_missing_leadtime(args):
    args.leadtime = None
    with (
        patch.object(upp, "parse_args", return_value=args),
        pytest.raises(TypeError),
    ):
        upp.main()
