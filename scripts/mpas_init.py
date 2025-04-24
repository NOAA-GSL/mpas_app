#!/usr/bin/env python3

"""
The run script for the mpas init_atmosphere.
"""

import os
import sys
from datetime import datetime
from pathlib import Path

from uwtools.api.logging import use_uwtools_logger
from uwtools.api.mpas_init import MPASInit


def main():
    use_uwtools_logger()

    # Load the YAML config
    config_path = os.environ["CONFIG_PATH"]
    expt_sect = os.environ["EXPT_SECT"]
    cycle = datetime.fromisoformat(os.environ["CYCLE"])

    # Run mpas_init
    mpas_init_driver = MPASInit(config=config_path, cycle=cycle, key_path=[expt_sect])
    mpas_init_driver.run()

    # Obtain MPAS init run directory path
    mpas_init_dir = Path(mpas_init_driver.config["rundir"])

    if not (mpas_init_dir / "runscript.mpas_init.done").is_file():
        print("Error occurred running mpas_init. Please see component error logs.")
        sys.exit(1)


if __name__ == "__main__":
    main()
