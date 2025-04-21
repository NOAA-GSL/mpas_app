"""
The run script for the mpas init_atmosphere
"""

import inspect
import os
import sys
from datetime import datetime
from pathlib import Path
from subprocess import STDOUT, CalledProcessError, check_output

from uwtools.api import config as uwconfig
from uwtools.api.mpas_init import MPASInit
from uwtools.api.logging import use_uwtools_logger

from utils import run_shell_cmd

def parse_args(argv):
    """
    Parse arguments for the script.
    """
    parser = ArgumentParser(
        description="Script that runs UPP via uwtools API.",
    )
    parser.add_argument(
        "-c",
        "--config-file",
        metavar="PATH",
        required=True,
        help="Path to experiment config file.",
        type=Path,
    )
    parser.add_argument(
        "--cycle",
        help="The cycle in ISO8601 format (e.g. 2024-07-15T18).",
        required=True,
        type=dt.datetime.fromisoformat,
    )
    parser.add_argument(
        "--key-path",
        help="Dot-separated path of keys leading through the config to the driver's YAML block.",
        metavar="KEY[.KEY...]",
        required=True,
        type=lambda s: s.split("."),
    )
    return parser.parse_args(argv)


def run_mpas_init(config_file, cycle, key_path):
    """
    Setup and run the mpas_init UW Driver.
    """

    # Run mpas_init
    mpas_init_driver = MPASInit(config=config_file, cycle=cycle, key_path=key_path)
    mpas_init_dir = Path(mpas_init_driver.config["rundir"])
    logging.info("Will run mpas_init in {mpas_init_dir}")
    mpas_init_driver.run()

    if not (mpas_init_dir / "runscript.mpas_init.done").is_file():
        print("Error occurred running mpas_init. Please see component error logs.")
        sys.exit(1)

    expt_config = load_yaml_config(config_file)
    external_model = expt_config["user"]["ics"]["external_model"]
    if external_model == "RRFS":
        # Switch out values from fix files
        variables_from_fix(expt_config, mpas_init_driver.config):

def variables_from_fix(expt_config, driver_config):
    """
    Call ncks for variables that should come from fix files
    """
    init_file = driver_config["streams"]["output"]["filename_template"]
    files_to_link = mpas_init_driver.config["files_to_link"]
    mesh_label = expt_config["user"]["mesh_label"]
    for variable in ("shdmax", "shdmin"):
        fix_file = files_to_link[f"{variable}.{mesh_label}.nc"]
        cmd = f"module load nco ; ncks -A -v {variable} {fix_file} {init_file}"
        run_shell_cmd(
            cmd=cmd,
            cwd=driver_config["rundir"],
            log_output=True,
            task_name.inspect.stack()[0][3],
            )


if __name__ == "__main__":

    use_uwtools_logger()


    args = parse_args(sys.argv[1:])
    run_mpas_init(
        config_file=args.config_file,
        cycle=args.cycle,
        key_path=args.key_path,
        member=args.member,
    )
