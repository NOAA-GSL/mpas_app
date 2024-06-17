"""
Creates the experiment directory and populates it with necessary configuration and workflow files.
"""

import argparse
import logging
import os
import sys
from pathlib import Path
from shutil import copy
from subprocess import STDOUT, CalledProcessError, check_output
from typing import Optional

import uwtools.api.config as uwconfig
import uwtools.api.rocoto as uwrocoto
from uwtools.config.formats.base import Config


def create_grid_files(expt_dir: Path, mesh_file_path: Path, nprocs: int) -> None:
    """
    Stage the mesh file in the experiment directory and decompose them for the current experiment.
    """
    copy(src=mesh_file_path, dst=expt_dir)
    mesh_file = expt_dir / mesh_file_path.name
    cmd = f"gpmetis -minconn -contig -niter=200 {mesh_file} {nprocs}"
    try:
        output = check_output(
            cmd, encoding="utf=8", shell=True, stderr=STDOUT, text=True
        )
    except CalledProcessError as e:
        output = e.output
        print("Error running command:")
        print(f"  {cmd}")
        for line in output.split("\n"):
            print(line)
        print(f"Failed with status: {e.returncode}")
        sys.exit(1)


def main(user_config_files: list[Path, str]) -> None:
    """
    Stage the Rocoto XML and experiment YAML in the desired experiment
    directory.
    """

    # Set up the experiment
    mpas_app = Path(os.path.dirname(__file__)).parent.absolute()
    experiment_config = uwconfig.get_yaml_config(Path("./default_config.yaml"))
    user_config = None
    for cfg_file in user_config_files:
        cfg = uwconfig.get_yaml_config(cfg_file)
        if not user_config:
            user_config = cfg
            continue
        user_config.update_values(cfg)

    machine = user_config["user"]["platform"]
    platform_config = uwconfig.get_yaml_config(mpas_app / "parm" / "machines" / f"{machine}.yaml")

    for supp_config in (platform_config, user_config):
        experiment_config.update_values(supp_config)
    print(experiment_config)

    experiment_config["user"]["mpas_app"] = mpas_app.as_posix()

    # Build the experiment directory
    experiment_path = Path(experiment_config["user"]["experiment_dir"])
    print("Experiment will be set up here: {}".format(experiment_path))
    os.makedirs(experiment_path, exist_ok=True)

    experiment_file = experiment_path / "experiment.yaml"

    # Load the workflow definition
    workflow_blocks = experiment_config["user"]["workflow_blocks"]
    workflow_blocks = [mpas_app / "parm" / "wflow" / b for b in workflow_blocks]

    for workflow_block in workflow_blocks:
        block_config = uwconfig.get_yaml_config(workflow_block)
        experiment_config.update_values(block_config)

    uwconfig.realize(
        input_config=experiment_config,
        output_file=experiment_file,
        update_config={},
    )

    # Create the workflow files
    rocoto_xml = experiment_path / "rocoto.xml"
    rocoto_valid = uwrocoto.realize(config=experiment_file, output_file=rocoto_xml)
    if not rocoto_valid:
        sys.exit(1)

    # Create grid files
    mesh_file_name = f"{experiment_config['user']['mesh_label']}.graph.info"
    mesh_file_path = Path(experiment_config["data"]["mesh_files"]) / mesh_file_name

    all_nprocs = []
    for sect, driver in (
        ("create_ics", "mpas_init"),
        ("create_lbcs", "mpas_init"),
        ("forecast", "mpas"),
        ):
        resources = experiment_config[sect][driver]["execution"]["batchargs"]
        if (cores := resources.get("cores")) is None:
            cores = resources["nodes"] * resources["tasks_per_node"]
        all_nprocs.append(cores)
    for nprocs in set(all_nprocs):
        print(f"Creating grid file for {nprocs} procs")
        create_grid_files(experiment_path, mesh_file_path, nprocs)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Configure an experiment with the following input:"
    )
    parser.add_argument(
            "user_config_files",
            nargs="+",
            help="Paths to the user config files.")

    args = parser.parse_args()
    main(user_config_files=Path(args.user_config_files))
