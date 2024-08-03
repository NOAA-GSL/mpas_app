"""
The run script for ungrib
"""

import os
import sys
from datetime import datetime
from pathlib import Path

from uwtools.api import config as uwconfig
from uwtools.api import ungrib


# Load the YAML config
CONFIG_PATH = os.environ["CONFIG_PATH"]
CYCLE = os.environ["CYCLE"]

cycle = datetime.fromisoformat(CYCLE)

# Extract driver config from experiment config
expt_config = uwconfig.get_yaml_config(CONFIG_PATH)
expt_config.dereference(context={"cycle": cycle, **expt_config})

ungrib_config = expt_config["prepare_grib"]["ungrib"]
ungrib_dir = Path(ungrib_config["rundir"])

# Run ungrib
ungrib.execute(task="run", config=CONFIG_PATH, cycle=cycle,
        key_path=["prepare_grib"])

if not (ungrib_dir / "runscript.ungrib.done").is_file():
    print("Error occurred running ungrib. Please see component error logs.")
    sys.exit(1)
