#!/usr/bin/env python3
"""
The run script for ungrib.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from uwtools.api.logging import use_uwtools_logger
from uwtools.api.ungrib import Ungrib

from scripts.common import check_success, parse_args, run_component


def main():
    use_uwtools_logger()
    args = parse_args()
    driver = Ungrib
    rundir = run_component(
        driver_class=driver,
        config_file=args.config_file,
        cycle=args.cycle,
        key_path=args.key_path,
    )
    check_success(rundir, driver.driver_name())


if __name__ == "__main__":
    main()  # pragma: no cover
