from __future__ import annotations

import logging
import sys
from argparse import ArgumentParser, Namespace
from datetime import datetime, timedelta, timezone
from pathlib import Path

from uwtools.api.logging import use_uwtools_logger

# Public functions


def parse_args(argv=None, *, lead_required: bool = False) -> Namespace:
    parser = ArgumentParser(description="Common driver script parser.")
    parser.add_argument(
        "-c", "--config-file", required=True, type=Path, help="Path to config file."
    )
    parser.add_argument("--cycle", required=True, type=_utc, help="Cycle in ISO8601 format.")
    parser.add_argument(
        "--leadtime",
        required=lead_required,
        type=lambda x: timedelta(hours=int(x)),
        help="Lead time in hours.",
    )
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
    leadtime: timedelta | None = None,
) -> type:
    use_uwtools_logger()
    kwargs = {"config": config_file, "cycle": cycle, "key_path": key_path}
    if leadtime is not None:
        kwargs["leadtime"] = leadtime
    driver = driver_class(**kwargs)
    rundir = Path(driver.config["rundir"])
    logging.info("Running %s in %s", driver_class.__name__, rundir)
    task = driver.run()
    if not task.ready:
        logging.error("Error occurred. Expected file %s not found.", task.refs[0])
        sys.exit(1)
    return driver


# Private functions


def _utc(date_string) -> datetime:
    return datetime.fromisoformat(date_string).replace(tzinfo=timezone.utc)
