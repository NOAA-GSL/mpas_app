"""
The run script for ungrib
"""
import os
import tempfile
from datetime import datetime
from pathlib import Path

import yaml

import uwtools.api.config as uwconfig
import uwtools.api.ungrib as ungrib


# Load the YAML config
CONFIG_PATH = os.environ["CONFIG_PATH"]
CYCLE = os.environ["CYCLE"]

cycle = datetime.fromisoformat(CYCLE)

# Extract driver config from experiment config and save in the run directory
expt_config = uwconfig.get_yaml_config(CONFIG_PATH)
expt_config.dereference(context={"cycle": cycle, **expt_config})


ungrib_config = expt_config["prepare_grib"]
ungrib_config.update({"platform": expt_config["platform"], "user": expt_config["user"]})
ungrib_config = uwconfig.get_yaml_config(ungrib_config)

ungrib_yaml = Path(ungrib_config["ungrib"]["run_dir"]) / "ungrib.yaml"
ungrib_yaml.parent.mkdir(parents=True, exist_ok=True)
ungrib_config.dump(path=ungrib_yaml)

# Run ungrib
ungrib.execute(task="run", config=ungrib_yaml, cycle=cycle)
