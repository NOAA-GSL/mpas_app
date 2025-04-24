#!/usr/bin/env python3

"""
The run script for the mpas forecast.
"""

import os
import sys
from datetime import datetime
from pathlib import Path

from uwtools.api.logging import use_uwtools_logger
from uwtools.api.mpas import MPAS


def main():
    use_uwtools_logger()

    # Load the YAML config
    config_path = os.environ["CONFIG_PATH"]
    cycle = datetime.fromisoformat(os.environ["CYCLE"])

    # Run mpas
    mpas_driver = MPAS(config=config_path, cycle=cycle, key_path=["forecast"])
    mpas_driver.run()

    # Obtain run directory path
    mpas_dir = Path(mpas_driver.config["rundir"])

    if not (mpas_dir / "runscript.mpas.done").is_file():
        print("Error occurred running mpas. Please see component error logs.")
        sys.exit(1)


if __name__ == "__main__":
    main()
