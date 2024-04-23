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

# Extract driver config from experiment config and save in the run directory
expt_config = uwconfig.get_yaml_config(CONFIG_PATH)
expt_config.dereference(context={"cycle": cycle, **expt_config})


mpas_config = expt_config["forecast"]
mpas_config.update({"platform": expt_config["platform"], "user": expt_config["user"]})
mpas_config = uwconfig.get_yaml_config(mpas_config)

mpas_dir = Path(mpas_config["mpas"]["run_dir"])
mpas_yaml = mpas_dir / "mpas.yaml"
mpas_yaml.parent.mkdir(parents=True, exist_ok=True)
mpas_config.dump(path=mpas_yaml)

# Run mpas
mpas.execute(task="run", config=mpas_yaml, cycle=cycle)

if not (mpas_dir / "done.mpas").is_file():
    print("Error occurred running mpas. Please see component error logs.")
    sys.exit(1)
