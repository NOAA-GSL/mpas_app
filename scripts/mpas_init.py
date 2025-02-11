"""
The run script for the mpas init_atmosphere
"""

import os
import sys
from datetime import datetime
from pathlib import Path

from uwtools.api import config as uwconfig
from uwtools.api import mpas_init
from uwtools.api.logging import use_uwtools_logger

use_uwtools_logger()


# Load the YAML config
CONFIG_PATH = os.environ["CONFIG_PATH"]
CYCLE = os.environ["CYCLE"]
EXPT_SECT = os.environ["EXPT_SECT"]

cycle = datetime.fromisoformat(CYCLE)

# Run mpas_init
mpas_init.execute(task="run", config=CONFIG_PATH, cycle=cycle,
        key_path=[EXPT_SECT])

# Extract driver config from experiment config
expt_config = uwconfig.get_yaml_config(CONFIG_PATH)
expt_config.dereference(context={"cycle": cycle, **expt_config})

mpas_init_dir = Path(expt_config[EXPT_SECT]["mpas_init"]["rundir"])

if not (mpas_init_dir / "runscript.mpas_init.done").is_file():
    print("Error occurred running mpas_init. Please see component error logs.")
    sys.exit(1)
