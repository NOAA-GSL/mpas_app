#!/usr/bin/env python3

"""
Creates the experiment directory and populates it with necessary configuration and workflow files.
"""

import argparse
import sys
from pathlib import Path
from shutil import copy
from subprocess import STDOUT, CalledProcessError, check_output

from uwtools.api import rocoto
from uwtools.api.config import get_yaml_config, realize
from uwtools.api.logging import use_uwtools_logger

sys.path.append(str(Path(__file__).parent.parent))

from ush.validation import validate


def create_grid_files(expt_dir: Path, mesh_file_path: Path, nprocs: int) -> None:
    """
    Stage the mesh file in the experiment directory and decompose them for the current experiment.
    """
    copy(src=mesh_file_path, dst=expt_dir)
    mesh_file = expt_dir / mesh_file_path.name
    cmd = f"gpmetis -minconn -contig -niter=200 {mesh_file} {nprocs}"
    try:
        output = check_output(cmd, encoding="utf=8", shell=True, stderr=STDOUT, text=True)
    except CalledProcessError as e:
        output = e.output
        print("Error running command:")
        print(f"  {cmd}")
        for line in output.split("\n"):
            print(line)
        print(f"Failed with status: {e.returncode}")
        sys.exit(1)


def main(user_config_files):
    """
    Stage the Rocoto XML and experiment YAML in the desired experiment
    directory.
    """

    # Set up the experiment
    experiment_config = get_yaml_config(Path("./default_config.yaml"))
    user_config = get_yaml_config({})
    for cfg_file in user_config_files:
        cfg = get_yaml_config(cfg_file)
        user_config.update_from(cfg)
        experiment_config.update_from(cfg)

    mpas_app = Path(__file__).parent.parent.resolve()
    machine = experiment_config["user"]["platform"]
    platform_config = get_yaml_config(mpas_app / "parm" / "machines" / f"{machine}.yaml")

    # Updates based on user-selected external_models
    external_model_config = get_yaml_config(mpas_app / "ush" / "external_model_config.yaml")
    for bcs in ("ics", "lbcs"):
        model = experiment_config["user"][bcs]["external_model"]
        bcs_config = external_model_config[model][bcs]
        experiment_config.update_from(bcs_config)

    # Make sure user_config is last to override any settings from supplementals
    for supp_config in (platform_config, user_config):
        experiment_config.update_from(supp_config)

    experiment_config.dereference()
    user_block = validate(experiment_config.as_dict()).user

    # Build the experiment directory
    experiment_dir = user_block.experiment_dir
    print(f"Experiment will be set up here: {experiment_dir}")
    Path(experiment_dir).mkdir(parents=True, exist_ok=True)

    experiment_file = experiment_dir / "experiment.yaml"

    # Load the workflow definition
    workflow_blocks = [mpas_app / "parm" / "wflow" / b for b in user_block.workflow_blocks]

    workflow_config = get_yaml_config({})
    for workflow_block in workflow_blocks:
        workflow_config.update_from(get_yaml_config(workflow_block))
    workflow_config.update_from(dict(user_block))

    realize(input_config=workflow_config, output_file=experiment_file, update_config={})

    # Create the workflow files
    rocoto_xml = experiment_dir / "rocoto.xml"
    rocoto_valid = rocoto.realize(config=experiment_file, output_file=rocoto_xml)
    if not rocoto_valid:
        sys.exit(1)

    # Create grid files
    mesh_file_name = f"{user_block.mesh_label}.graph.info"
    mesh_file_path = Path(experiment_config["data"]["mesh_files"]) / mesh_file_name

    all_nprocs = []
    for sect, driver in (
        ("create_ics", "mpas_init"),
        ("create_lbcs", "mpas_init"),
        ("forecast", "mpas"),
        ("post", "mpassit"),
    ):
        if sect in experiment_config:
            resources = experiment_config[sect][driver]["execution"]["batchargs"]
            if (cores := resources.get("cores")) is None:
                cores = resources["nodes"] * resources["tasks_per_node"]
            all_nprocs.append(cores)
    for nprocs in all_nprocs:
        if not (experiment_dir / f"{mesh_file_path.name}.part.{nprocs}").is_file():
            print(f"Creating grid file for {nprocs} procs")
            create_grid_files(experiment_dir, mesh_file_path, nprocs)


if __name__ == "__main__":
    use_uwtools_logger()

    parser = argparse.ArgumentParser(
        description="Configure an experiment with the following input:"
    )
    parser.add_argument("user_config_files", nargs="+", help="Paths to the user config files.")

    args = parser.parse_args()
    path_list = [Path(p) for p in args.user_config_files]
    main(user_config_files=path_list)
