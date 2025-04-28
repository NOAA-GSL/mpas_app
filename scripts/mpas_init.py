#!/usr/bin/env python3
"""
The run script for the MPAS init_atmosphere.
"""

import datetime as dt
import logging
import sys
from argparse import ArgumentParser
from pathlib import Path

from uwtools.api.logging import use_uwtools_logger
from uwtools.api.mpas_init import MPASInit


def parse_args(argv):
    """
    Parse arguments for the script.
    """
    parser = ArgumentParser(
        description="Script that runs mpas_init via uwtools API.",
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


def run_mpas_init(config_file, cycle, key_path):
    """
    Setup and run the mpas_init UW Driver.
    """

    # Run mpas_init
    mpas_init_driver = MPASInit(config=config_file, cycle=cycle, key_path=key_path)
    mpas_init_dir = Path(mpas_init_driver.config["rundir"])
    logging.info("Will run mpas_init in {mpas_init_dir}")
    mpas_init_driver.run()

    if not (mpas_init_dir / "runscript.mpas_init.done").is_file():
        print("Error occurred running mpas_init. Please see component error logs.")
        sys.exit(1)


if __name__ == "__main__":

    use_uwtools_logger()


    args = parse_args(sys.argv[1:])
    run_mpas_init(
        config_file=args.config_file,
        cycle=args.cycle,
        key_path=args.key_path,
    )
