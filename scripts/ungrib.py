"""
The run script for ungrib
"""

import os
import sys
from datetime import datetime
from pathlib import Path

from uwtools.api import config as uwconfig
from uwtools.api.ungrib import Ungrib
from uwtools.api.logging import use_uwtools_logger

use_uwtools_logger()


# Load the YAML config
CONFIG_PATH = os.environ["CONFIG_PATH"]
CYCLE = os.environ["CYCLE"]

cycle = datetime.fromisoformat(CYCLE)

# Run ungrib
ungrib_driver = Ungrib(config=CONFIG_PATH, cycle=cycle, key_path=["prepare_grib"])
ungrib_driver.run()

# Obtain ungrib run directory path
ungrib_dir = Path(ungrib_driver.config["rundir"])

if not (ungrib_dir / "runscript.ungrib.done").is_file():
    print("Error occurred running ungrib. Please see component error logs.")
    sys.exit(1)
