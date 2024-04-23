"""
The run script for the mpas init_atmosphere
"""

import os
import sys
from datetime import datetime
from pathlib import Path

from uwtools.api import config as uwconfig
from uwtools.api import mpas_init


# Load the YAML config
CONFIG_PATH = os.environ["CONFIG_PATH"]
CYCLE = os.environ["CYCLE"]
EXPT_SECT = os.environ["EXPT_SECT"]

cycle = datetime.fromisoformat(CYCLE)

# Extract driver config from experiment config and save in the run directory
expt_config = uwconfig.get_yaml_config(CONFIG_PATH)
expt_config.dereference(context={"cycle": cycle, **expt_config})


mpas_init_config = expt_config[EXPT_SECT]
mpas_init_config.update({"platform": expt_config["platform"], "user": expt_config["user"]})
mpas_init_config = uwconfig.get_yaml_config(mpas_init_config)

mpas_init_dir = Path(mpas_init_config["mpas_init"]["run_dir"])
mpas_init_yaml = mpas_init_dir / "mpas_init.yaml"
mpas_init_yaml.parent.mkdir(parents=True, exist_ok=True)
mpas_init_config.dump(path=mpas_init_yaml)

# Run mpas_init
mpas_init.execute(task="run", config=mpas_init_yaml, cycle=cycle)

if not (mpas_init_dir / "done.mpas_init").is_file():
    print("Error occurred running mpas_init. Please see component error logs.")
    sys.exit(1)
