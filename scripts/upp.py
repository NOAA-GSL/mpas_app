"""
The runscript for UPP
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

from uwtools.api import config as uwconfig
from uwtools.api.upp import UPP


# Load the YAML config
CONFIG_PATH = os.environ["CONFIG_PATH"]
CYCLE = os.environ["CYCLE"]
LEAD = timedelta(hours=int(os.environ["LEAD"]))

cycle = datetime.fromisoformat(CYCLE)

# Run UPP
upp_driver = UPP(config=CONFIG_PATH, cycle=cycle, leadtime=LEAD, key_path=["post"])
upp_driver.run()

# Extract driver config from experiment config
# expt_config = uwconfig.get_yaml_config(CONFIG_PATH)
# expt_config.dereference(context={"cycle": cycle, "leadtime": LEAD, **expt_config})

# Obtain run directory path
upp_dir = Path(upp_driver.config["rundir"])

# driver_config = expt_config["post"]["upp"]
# rundir = Path(driver_config["rundir"])
# print(f"Will run in {rundir}")

# Run upp
# upp.execute(task="run", config=CONFIG_PATH, cycle=cycle, key_path=["post"], leadtime=LEAD)
if not (upp_dir / "runscript.upp.done").is_file():
    print("Error occurred running UPP. Please see component error logs.")
    sys.exit(1)
