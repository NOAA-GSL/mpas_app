#!/usr/bin/env python
"""
The run script for ungrib.
"""

import datetime as dt
import logging
import sys
from argparse import ArgumentParser
from pathlib import Path

from uwtools.api.logging import use_uwtools_logger
from uwtools.api.ungrib import Ungrib


def parse_args(argv):
    """
    Parse arguments for the script.
    """
    parser = ArgumentParser(
        description="Script that runs UPP via uwtools API.",
    )
    parser.add_argument(
        "-c",
        "--config-file",
        metavar="PATH",
        required=True,
        help="Path to experiment config file.",
        type=Path,
    )
    parser.add_argument(
        "--cycle",
        help="The cycle in ISO8601 format (e.g. 2024-07-15T18).",
        required=True,
        type=dt.datetime.fromisoformat,
    )
    parser.add_argument(
        "--key-path",
        help="Dot-separated path of keys leading through the config to the driver's YAML block.",
        metavar="KEY[.KEY...]",
        required=True,
        type=lambda s: s.split("."),
    )
    return parser.parse_args(argv)


def run_ungrib(config_file, cycle, key_path):
    """
    Setup and run the ungrib driver.
    """
    # Run ungrib
    ungrib_driver = Ungrib(config=config_file, cycle=cycle, key_path=key_path)
    ungrib_dir = Path(ungrib_driver.config["rundir"])
    logging.info("Will run ungrib in %s", ungrib_dir)
    ungrib_driver.run()

    if not (ungrib_dir / "runscript.ungrib.done").is_file():
        print("Error occurred running ungrib. Please see component error logs.")
        sys.exit(1)


if __name__ == "__main__":

    use_uwtools_logger()

    args = parse_args(sys.argv[1:])
    run_ungrib(
        config_file=args.config_file,
        cycle=args.cycle,
        key_path=args.key_path,
        )
