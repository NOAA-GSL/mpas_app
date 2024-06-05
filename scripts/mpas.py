"""
The run script for the mpas forecast
"""

import os
import sys
from datetime import datetime
from pathlib import Path

from uwtools.api import config as uwconfig
from uwtools.api import mpas


# Load the YAML config
CONFIG_PATH = os.environ["CONFIG_PATH"]
CYCLE = os.environ["CYCLE"]

cycle = datetime.fromisoformat(CYCLE)

# Extract driver config from experiment config
expt_config = uwconfig.get_yaml_config(CONFIG_PATH)
expt_config.dereference(context={"cycle": cycle, **expt_config})

mpas_config = expt_config["forecast"]["mpas"]
mpas_dir = Path(mpas_config["run_dir"])

# Run mpas
mpas.execute(task="run", config=CONFIG_PATH, cycle=cycle, key_path["forecast"])

if not (mpas_dir / "runscript.mpas.done").is_file():
    print("Error occurred running mpas. Please see component error logs.")
    sys.exit(1)
