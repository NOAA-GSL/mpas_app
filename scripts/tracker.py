"""
The run script for UPP
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

from uwtools.api import config as uwconfig
from uwtools.api.driver import execute


# Load the YAML config
CONFIG_PATH = os.environ["CONFIG_PATH"]
CYCLE = os.environ["CYCLE"]

cycle = datetime.fromisoformat(CYCLE)
key_path = "tracker"

# Extract driver config from experiment config
expt_config = uwconfig.get_yaml_config(CONFIG_PATH)
expt_config.dereference(context={"cycle": cycle, **expt_config})

driver_dir = Path(expt_config["user"]["mpas_app"], "drivers")

driver_config = expt_config[key_path]["tracker"]
rundir = Path(driver_config["rundir"])
print(f"Will run in {rundir}")

# Run the tracker
execute(
    module=driver_dir / "tracker.py",
    classname="GFDLTracker",
    task="run",
    schema_file=driver_dir / "tracker.jsonschema",
    config=CONFIG_PATH,
    cycle=cycle,
    key_path=[key_path],
)

if not (rundir / "runscript.gfdl-tracker.done").is_file():
    print("Error occurred running the GFDL Vortex Tracker. Please see component error logs.")
    sys.exit(1)
