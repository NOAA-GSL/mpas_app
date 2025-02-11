"""
The run script for ungrib
"""

import os
import sys
from datetime import datetime
from pathlib import Path

from uwtools.api import config as uwconfig
from uwtools.api import ungrib
from uwtools.api.logging import use_uwtools_logger

use_uwtools_logger()


# Load the YAML config
CONFIG_PATH = os.environ["CONFIG_PATH"]
CYCLE = os.environ["CYCLE"]

cycle = datetime.fromisoformat(CYCLE)

# Run ungrib
ungrib.execute(task="run", config=CONFIG_PATH, cycle=cycle,
        key_path=["prepare_grib"])

# Extract driver config from experiment config
expt_config = uwconfig.get_yaml_config(CONFIG_PATH)
expt_config.dereference(context={"cycle": cycle, **expt_config})

ungrib_dir = Path(expt_config["prepare_grib"]["ungrib"]["rundir"])

if not (ungrib_dir / "runscript.ungrib.done").is_file():
    print("Error occurred running ungrib. Please see component error logs.")
    sys.exit(1)
