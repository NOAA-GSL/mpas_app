from __future__ import annotations

import logging
import sys
from argparse import ArgumentParser
from datetime import datetime, timedelta, timezone
from pathlib import Path

from uwtools.api.logging import use_uwtools_logger

use_uwtools_logger()


def utc(date_string):
    return datetime.fromisoformat(date_string).replace(tzinfo=timezone.utc)


def parse_args(argv=None):
    parser = ArgumentParser(description="Common driver script parser.")
    parser.add_argument(
        "-c", "--config-file", required=True, type=Path, help="Path to config file."
    )
    parser.add_argument("--cycle", required=True, type=utc, help="Cycle in ISO8601 format.")
    parser.add_argument("--lead", type=int, help="Lead time in hours.")
    parser.add_argument(
        "--key-path",
        required=True,
        type=lambda s: s.split("."),
        help="Dot-separated key path, e.g., forecast or post.processing.",
    )
    return parser.parse_args(argv)


def run_component(
    driver_class: type,
    config_file: Path,
    cycle: datetime,
    key_path: list[str],
    lead: timedelta | None = None,
) -> Path:
    kwargs = {"config": str(config_file), "cycle": cycle, "key_path": key_path}
    if lead:
        kwargs["leadtime"] = lead
    driver = driver_class(**kwargs)
    rundir = Path(driver.config["rundir"])
    logging.info("Running %s in %s", driver_class.__name__, rundir)
    driver.run()
    return rundir


def check_success(rundir: Path, done_file: str):
    done_path = rundir / done_file
    if not done_path.is_file():
        print(f"Error occurred. Expected file '{done_file}' not found in {rundir}.")
        sys.exit(1)
