#!/usr/bin/env python3

"""
The run script for ungrib.
"""

import os
import sys
from datetime import datetime
from pathlib import Path

from uwtools.api.logging import use_uwtools_logger
from uwtools.api.ungrib import Ungrib


def main():
    use_uwtools_logger()

    # Load the YAML config
    config_path = os.environ["CONFIG_PATH"]
    key_path = os.environ["KEY_PATH"]
    cycle = datetime.fromisoformat(os.environ["CYCLE"])

    # Run ungrib
    ungrib_driver = Ungrib(config=config_path, cycle=cycle, key_path=[key_path])
    ungrib_driver.run()

    # Obtain ungrib run directory path
    ungrib_dir = Path(ungrib_driver.config["rundir"])

    if not (ungrib_dir / "runscript.ungrib.done").is_file():
        print("Error occurred running ungrib. Please see component error logs.")
        sys.exit(1)


if __name__ == "__main__":
    main()
