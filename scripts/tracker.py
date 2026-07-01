#!/usr/bin/env python3
"""
The run script for the GFDL Vortex Tracker.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from uwtools.api.config import get_yaml_config
from uwtools.api.logging import use_uwtools_logger

from drivers.tracker import GFDLTracker
from scripts.common import parse_args, run_component


def main():
    args = parse_args()
    use_uwtools_logger()
    expt_config = get_yaml_config(args.config_file)
    driver_dir = Path(expt_config["user"]["mpas_app"], "drivers")

    # Run the tracker
    run_component(
        driver_class=GFDLTracker,
        config_file=args.config_file,
        cycle=args.cycle,
        key_path=args.key_path,
        schema_file=driver_dir / "tracker.jsonschema",
    )


if __name__ == "__main__":
    main()  # pragma: no cover
