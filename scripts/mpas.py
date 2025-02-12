"""
The run script for the mpas forecast
"""

import os
import sys
from datetime import datetime
from pathlib import Path

from uwtools.api import config as uwconfig
from uwtools.api import mpas
from uwtools.api.logging import use_uwtools_logger

use_uwtools_logger()


# Load the YAML config
CONFIG_PATH = os.environ["CONFIG_PATH"]
CYCLE = os.environ["CYCLE"]

cycle = datetime.fromisoformat(CYCLE)

# Run mpas
mpas.execute(task="run", config=CONFIG_PATH, cycle=cycle, key_path=["forecast"])

# Transform experiment config and obtain MPAS run directory path
expt_config = uwconfig.get_yaml_config(CONFIG_PATH)
expt_config.dereference(context={"cycle": cycle, **expt_config})

mpas_dir = Path(expt_config["forecast"]["mpas"]["rundir"])

if not (mpas_dir / "runscript.mpas.done").is_file():
    print("Error occurred running mpas. Please see component error logs.")
    sys.exit(1)
