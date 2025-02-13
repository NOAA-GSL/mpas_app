"""
The run script for the mpas init_atmosphere
"""

import os
import sys
from datetime import datetime
from pathlib import Path

from uwtools.api import config as uwconfig
from uwtools.api.mpas_init import MPASInit
from uwtools.api.logging import use_uwtools_logger

use_uwtools_logger()


# Load the YAML config
CONFIG_PATH = os.environ["CONFIG_PATH"]
CYCLE = os.environ["CYCLE"]
EXPT_SECT = os.environ["EXPT_SECT"]

cycle = datetime.fromisoformat(CYCLE)

# Run mpas_init
mpas_init_driver = MPASInit(config=CONFIG_PATH, cycle=cycle, key_path=[EXPT_SECT])
mpas_init_driver.run()

# Obtain MPAS init run directory path
mpas_init_dir = Path(mpas_init_driver.config["rundir"])

if not (mpas_init_dir / "runscript.mpas_init.done").is_file():
    print("Error occurred running mpas_init. Please see component error logs.")
    sys.exit(1)
