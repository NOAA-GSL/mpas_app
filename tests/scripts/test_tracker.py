from pathlib import Path
from unittest.mock import patch

from scripts import tracker


def test_main(args):
    mpas_app = Path("/some/path")
    expt_config = {"user": {"mpas_app": str(mpas_app)}}
    with (
        patch.object(tracker, "get_yaml_config", return_value=expt_config),
        patch.object(tracker, "parse_args", return_value=args) as parse_args,
        patch.object(tracker, "run_component", return_value=Path("/some/rundir")) as run_component,
    ):
        tracker.main()
        parse_args.assert_called_once()
        run_component.assert_called_once_with(
            driver_class=tracker.GFDLTracker,
            config_file=args.config_file,
            cycle=args.cycle,
            key_path=args.key_path,
            schema_file=mpas_app / "drivers" / "tracker.jsonschema",
        )
