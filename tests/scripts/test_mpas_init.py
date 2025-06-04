from pathlib import Path
from unittest.mock import patch

from scripts import mpas_init


def test_main(args):
    with (
        patch.object(mpas_init, "parse_args", return_value=args) as parse_args,
        patch.object(
            mpas_init, "run_component", return_value=Path("/some/rundir")
        ) as run_component,
    ):
        mpas_init.main()
        parse_args.assert_called_once()
        run_component.assert_called_once_with(
            driver_class=mpas_init.MPASInit,
            config_file=args.config_file,
            cycle=args.cycle,
            key_path=args.key_path,
        )
