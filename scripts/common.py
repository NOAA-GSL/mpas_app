import logging
import os
import sys
from argparse import ArgumentParser
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Type

from uwtools.api.logging import use_uwtools_logger

use_uwtools_logger()


def parse_common_args(argv=None):
    parser = ArgumentParser(description="Common driver script parser.")
    parser.add_argument(
        "-c", "--config-file", required=True, type=Path, help="Path to config file."
    )
    parser.add_argument(
        "--cycle", required=True, type=datetime.fromisoformat, help="Cycle in ISO8601 format."
    )
    parser.add_argument("--lead", type=int, help="Lead time in hours.")
    parser.add_argument(
        "--key-path",
        required=True,
        type=lambda s: s.split("."),
        help="Dot-separated key path, e.g., forecast or post.processing.",
    )
    return parser.parse_args(argv)


def run_component(
    driver_class: Type,
    config_file,
    cycle: datetime,
    key_path: list[str],
    lead: Optional[timedelta] = None,
) -> Path:
    kwargs = {"config": str(config_file), "cycle": cycle, "key_path": key_path}
    if lead:
        kwargs["leadtime"] = lead

    driver = driver_class(**kwargs)
    rundir = Path(driver.config["rundir"])
    logging.info("Running %s in %s", driver_class.__name__, rundir)
    driver.run()
    return rundir


def check_success_file(rundir: Path, done_filename: str):
    done_file = rundir / done_filename
    if not done_file.is_file():
        print(f"Error occurred. Expected file '{done_filename}' not found in {rundir}.")
        sys.exit(1)

