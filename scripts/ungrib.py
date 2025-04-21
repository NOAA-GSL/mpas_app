"""
The run script for ungrib
"""

import inspect
import os
import sys
from datetime import datetime
from pathlib import Path

from uwtools.api import config as uwconfig
from uwtools.api.ungrib import Ungrib
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

def regrid_winds(driver_config, task_config):
    """
    Use wgrib2 to regrid the winds.
    """
    wgrib_config = task_config["wgrib2"]
    budget_fields = Path(wgrib_config["budget_fields"]).read_text().strip()
    neighbor_fields = Path(wgrib_config["neighbor_fields"]).read_text().strip()
    options = [
        "-set_bitmap 1",
        "-set_grib_type c3",
        "-new_grid_winds grid",
        f"-new_grid_vectors {wgrib_config['grid_vectors']}",
        "-new_grid_interpolation bilinear",
        "-if \"{budget_fields}\" -new_grid_interpolation budget -fi",
        "-if \"{neighbor_fields}\" -new_grid_interpolation neighbor -fi",
        f"-new_grid {wgrib_config['grid_specs']}",
        ]
    for ingrib in glob.glob("GRIBFILE.*"):
        first_tmp = ingrib.resolve().stem + ".tmp.grib2"
        cmd = f"module load wgrib2 && wgrib2 {ingrib} {" ".join(options)} {first_tmp}"

        run_shell_cmd(
            cmd=cmd,
            cwd=driver_config["rundir"],
            log_output=True,
            task_name=inspect.stack()[0][3],
            )

        second_tmp = ingrib.resolve().stem + ".tmp2.grib2"
        cmd = (f"module load wgrib2 && wgrib2 {first_tmp}",
            f"-new_grid_vectors {wgrib_config['grid_vectors']}",
            f"-submsg_uv {second_tmp}",
            )
        run_shell_cmd(
            cmd=cmd,
            cwd=driver_config["rundir"],
            log_output=True,
            task_name=inspect.stack()[0][3],
            )
        ingrib.unlink()
        ingrib.symlink_to(second_tmp)


def run_ungrib(config_file, cycle, key_path):

    """
    Setup and run the ungrib driver.
    """
    expt_config = load_yaml_config(config_file)
    external_model = expt_config["user"]["ics"]["external_model"]

    # Run ungrib
    ungrib_driver = Ungrib(config=config_file, cycle=cycle, key_path=key_path)
    ungrib_dir = Path(ungrib_driver.config["rundir"])
    logging.info(f"Will run ungrib in {ungrib_dir}")
    if external_model == "RRFS":
        ungrib_driver.gribfiles()
        regrid_winds(ungrib_driver.config, expt_config)
    ungrib_driver.run()

    if not (ungrib_dir / "runscript.ungrib.done").is_file():
        print("Error occurred running ungrib. Please see component error logs.")
        sys.exit(1)


if __name__ == "__main__":

    use_uwtools_logger()

    args = parse_args(sys.argv[1:])
    run_ungrib(
        config_file=args.config_file,
        cycle=args.cycle,
        leadtime=args.leadtime,
        key_path=args.key_path,
        member=args.member,
