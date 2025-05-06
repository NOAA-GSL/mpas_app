#!/usr/bin/env python3

"""
The runscript for UPP.
"""

from uwtools.api.logging import use_uwtools_logger
from uwtools.api.upp import UPP

from scripts.common import check_success, parse_args, run_component


def main():
    """
    Setup and run the ungrib driver.
    """
    use_uwtools_logger()
    args = parse_args()
    rundir = run_component(
        driver_class=UPP,
        config_file=args.config_file,
        cycle=args.cycle,
        lead=args.lead,
        key_path=args.key_path,
    )
    check_success(rundir, "runscript.upp.done")


if __name__ == "__main__":
    main()  # pragma: no cover
