#!/usr/bin/env python3

"""
Creates the experiment directory and populates it with necessary configuration and workflow files.
"""

import argparse
import inspect
import logging
import sys
from datetime import timedelta
from pathlib import Path
from shutil import copy
from subprocess import STDOUT, CalledProcessError, check_output

from uwtools.api import rocoto
from uwtools.api.config import YAMLConfig, get_yaml_config, realize
from uwtools.api.driver import yaml_keys_to_classes
from uwtools.api.logging import use_uwtools_logger

sys.path.append(str(Path(__file__).parent.parent))

from ush.validation import Config, validate


def create_grid_files(expt_dir: Path, mesh_file_path: Path, nprocs: int) -> None:
    """
    Stage the mesh file in the experiment directory and decompose them for the current experiment.
    """
    copy(src=mesh_file_path, dst=expt_dir)
    mesh_file = expt_dir / mesh_file_path.name
    cmd = f"gpmetis -minconn -contig -niter=200 {mesh_file} {nprocs}"
    try:
        check_output(cmd, encoding="utf=8", shell=True, stderr=STDOUT, text=True)
    except CalledProcessError as e:
        logging.error("Error running command:")
        logging.error("  %s", cmd)
        for line in e.output.splitlines():
            logging.error(line)
        logging.error("Failed with status: %s", e.returncode)
        sys.exit(1)


def generate_workflow_files(
    experiment_config: YAMLConfig, experiment_file: Path, mpas_app: Path, validated: Config
):
    """
    Generate the Rocoto XML and the experiment YAML.
    """
    workflow_blocks = [mpas_app / "parm" / "wflow" / b for b in validated.user.workflow_blocks]
    workflow_config = get_yaml_config({})
    for block in workflow_blocks:
        workflow_config.update_from(get_yaml_config(block))
    workflow_config.update_from(experiment_config)
    validate_driver_blocks(validated.user.driver_validation_blocks, workflow_config)
    realize(
        input_config=workflow_config,
        output_file=experiment_file,
        update_config={"user": {"mpas_app": str(mpas_app)}},
    )
    rocoto_xml = experiment_file.parent / "rocoto.xml"
    rocoto_valid = rocoto.realize(config=experiment_file, output_file=rocoto_xml)
    if not rocoto_valid:
        logging.error("Invalid Rocoto XML")
        sys.exit(1)


def main():
    """
    Stage the Rocoto XML and experiment YAML in the experiment directory.
    """
    user_config_files = parse_args()
    experiment_config, mpas_app = prepare_configs(user_config_files)
    validated = validate(experiment_config.as_dict())
    experiment_dir, experiment_file = setup_experiment_directory(validated)
    generate_workflow_files(experiment_config, experiment_file, mpas_app, validated)
    stage_grid_files(experiment_config, experiment_dir, validated)


def parse_args() -> list[Path]:
    """
    Parse command-line arguments.
    """
    use_uwtools_logger()
    parser = argparse.ArgumentParser(
        description="Configure an experiment with the following input:"
    )
    parser.add_argument("user_config_files", nargs="+", help="Paths to the user config files.")
    return [Path(p) for p in parser.parse_args().user_config_files]


def prepare_configs(user_config_files: list[Path]) -> tuple[YAMLConfig, Path]:
    """
    Combine base, user, platform, and external model configs into one experiment config.
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
    return experiment_config, mpas_app


def required_nprocs(experiment_config: YAMLConfig) -> list[int]:
    """
    Get the processor count required for relevant workflow sections.
    """
    sections = [
        ("create_ics", "mpas_init"),
        ("create_lbcs", "mpas_init"),
        ("forecast", "mpas"),
        ("post", "mpassit"),
    ]
    nprocs = []
    for section, driver in sections:
        if section in experiment_config:
            resources = experiment_config[section][driver]["execution"]["batchargs"]
            cores = resources.get("cores") or (resources["nodes"] * resources["tasks_per_node"])
            nprocs.append(cores)
    return nprocs


def setup_experiment_directory(validated: Config) -> tuple[Path, Path]:
    """
    Create the experiment directory and write experiment.yaml.
    """
    experiment_dir = validated.user.experiment_dir
    logging.info("Experiment will be set up here: %s", experiment_dir)
    experiment_dir.mkdir(parents=True, exist_ok=True)
    experiment_file = experiment_dir / "experiment.yaml"
    return experiment_dir, experiment_file


def stage_grid_files(
    experiment_config: YAMLConfig, experiment_dir: Path, validated: Config
) -> None:
    """
    Create grid files for each required processor count, if they don't already exist.
    """
    mesh_file_name = f"{validated.user.mesh_label}.graph.info"
    mesh_file_path = Path(experiment_config["data"]["mesh_files"]) / mesh_file_name
    for nprocs in required_nprocs(experiment_config):
        part_file = experiment_dir / f"{mesh_file_path.name}.part.{nprocs}"
        if not part_file.is_file():
            logging.info("Creating grid file for %s procs", nprocs)
            create_grid_files(experiment_dir, mesh_file_path, nprocs)


def validate_driver_blocks(validated_blocks: list[str], workflow_config: YAMLConfig) -> None:
    """
    Validate driver configuration blocks in workflow config.
    """
    yaml_to_class_map = yaml_keys_to_classes()
    for block in validated_blocks:
        section, driver_name = block.rsplit(".", 1)
        driver_class = yaml_to_class_map[driver_name]
        kwargs = {
            "config": workflow_config,
            "cycle": workflow_config["user"]["first_cycle"],
            "key_path": section.split("."),
        }
        if "leadtime" in inspect.signature(driver_class).parameters:
            # hours=0 is an arbitrary number for validation purposes.
            kwargs["leadtime"] = timedelta(hours=0)
        driver_class(**kwargs)


if __name__ == "__main__":
    main()  # pragma: no cover
