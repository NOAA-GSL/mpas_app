"""
Creates the experiment directory and populates it with necessary configuration and workflow files.
"""

import argparse
import os
import sys

from importlib import resources
from pathlib import Path
from typing import Any, Dict, Optional, Type

from lxml import etree
import yaml

from pathlib import Path
from typing import Optional

import uwtools.api.config as uwconfig
import uwtools.api.rocoto as uwrocoto

def update_config(base_file: Path, new_values: Optional[Dict[str, Any]]):

    if not new_values:
        new_values = {}
    config_obj = uwconfig.get_yaml_config(base_file)
    config_obj.update_values(new_values)
    config_obj.dereference()
    return config_obj

def main(user_config_file: Optional[Path]) -> None:

    # Set up the experiment
    experiment_config = uwconfig.get_yaml_config(Path("./default_config.yaml"))
    user_config = uwconfig.get_yaml_config(user_config_file)
    experiment_config.update_values(user_config)

    experiment_config["user"]["mpas_app"] = Path(os.path.dirname(__file__)).parent.absolute().as_posix()
    experiment_config.dereference()

    # Build the experiment directory
    experiment_path = Path(experiment_config["user"]["experiment_dir"])
    os.makedirs(experiment_path, exist_ok=True)

    experiment_config.dump(experiment_path / "experiment.yaml")

    # Load the workflow definition
    default_workflow = Path("../parm/wflow/cold_start.yaml")
    rocoto_yaml_path = experiment_path / "rocoto.yaml"
    workflow_config = update_config(default_workflow, experiment_config)
    workflow_config.dump_dict(path=rocoto_yaml_path, cfg={"workflow": workflow_config["workflow"]})

    print(yaml.dump(workflow_config["user"]))

    # Create the workflow files
    rocoto_xml = experiment_path / "rocoto.xml"
    rocoto_valid = uwrocoto.realize(config=rocoto_yaml_path,
            output_file=rocoto_xml)
    if not rocoto_valid:
        sys.exit(1)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Configure an experiment with the following input:"
    )
    parser.add_argument(
        "user_config_file",
        help="Path to the user config file."
    )
    args = parser.parse_args()
    main(user_config_file=Path(args.user_config_file))
