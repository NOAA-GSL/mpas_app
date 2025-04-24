"""
The run script for the mpas forecast
"""

import os
import sys
from datetime import datetime
from pathlib import Path

from uwtools.api.logging import use_uwtools_logger
from uwtools.api.mpas import MPAS

use_uwtools_logger()


# Load the YAML config
CONFIG_PATH = os.environ["CONFIG_PATH"]
CYCLE = os.environ["CYCLE"]

cycle = datetime.fromisoformat(CYCLE)

# Run mpas
mpas_driver = MPAS(config=CONFIG_PATH, cycle=cycle, key_path=["forecast"])
mpas_driver.run()

# Obtain run directory path
mpas_dir = Path(mpas_driver.config["rundir"])

if not (mpas_dir / "runscript.mpas.done").is_file():
    print("Error occurred running mpas. Please see component error logs.")
    sys.exit(1)
