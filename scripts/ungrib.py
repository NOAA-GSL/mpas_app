#!/usr/bin/env python
"""
The run script for ungrib
"""

import datetime as dt
import glob
import inspect
import logging
import sys
from argparse import ArgumentParser
from pathlib import Path

from iota import asset, task, tasks

from uwtools.api.config import get_yaml_config
from uwtools.api.ungrib import Ungrib
from uwtools.api.logging import use_uwtools_logger

from utils import run_shell_cmd, walk_key_path

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

@task
def regrid_input(infile: Path, wgrib_config: dict):
    """
    Use wgrib2 to regrid the input file winds.

    :param infile: Input file path.
    :param wgrib_config: User-provided configuration settings.
    """
    outfile = infile.resolve().stem + ".tmp.grib2"
    yield f"wgrib2 regrid {outfile}"
    yield asset(outfile, outfile.is_file)
    yield file(path=infile)
    budget_fields = Path(wgrib_config["budget_fields"]).read_text().strip()
    neighbor_fields = Path(wgrib_config["neighbor_fields"]).read_text().strip()
    options = [
        "-ncpu 8",
        "-set_bitmap 1",
        "-set_grib_type c3",
        "-new_grid_winds grid",
        f"-new_grid_vectors {wgrib_config['grid_vectors']}",
        "-new_grid_interpolation bilinear",
        f"-if \"{budget_fields}\" -new_grid_interpolation budget -fi",
        f"-if \"{neighbor_fields}\" -new_grid_interpolation neighbor -fi",
        f"-new_grid {wgrib_config['grid_specs']}",
        ]
    cmd = f"module load wgrib2 && rm -f {first_tmp} && wgrib2 {str(ingrib)} {' '.join(options)} {first_tmp}"
    run_shell_cmd(
        cmd=cmd,
        cwd=driver_config["rundir"],
        log_output=True,
        taskname=inspect.stack()[0][3],
        )

@task
def merge_vector_fields(infile: Path, wgrib_config: dict):
    """
    Use wgrib2 to merge vector fields.
    """
    yield f"wgrib2 merge vector fields {outfile}"
    yield asset(outfile, outfile.is_file)
    regrid_task = regrid_input(infile, wgrib_config)
    yield regrid_task
    # or refs(regrid_task)
    # iotaa.logcfg -- for iotaa output logging.

    cmd = (f"module load wgrib2 && rm -f {second_tmp} && wgrib2
            {regrid_task.refs}",
        f"-new_grid_vectors {wgrib_config['grid_vectors']}",
        f"-submsg_uv {second_tmp}",
        "-ncpu 8",
        )
    run_shell_cmd(
        cmd=cmd,
        cwd=driver_config["rundir"],
        log_output=True,
        taskname=inspect.stack()[0][3],
        )

@task
def link_to_regridded_grib(infile:Path , outfile: Path, wgrib_config: dict):
    """
    Update original link to point to regridded grib file.
    """
    outfile = infile.resolve().stem + ".tmp2.grib2"
    yield "ungrib: update link {infile} to {outfile}"
    # make it an asset
    yield infile.resolve() == outfile
    yield merge_vector_fields(infile, wgrib_config)
    infile.unlink()
    infile.symlink_to(outfile)

@tasks
def regrid_winds(driver_config, task_config):
    """
    Use wgrib2 to regrid the winds.
    """
    wgrib_config = task_config["wgrib2"]
    # yield name
    yield [link_to_regridded(ingrib, wgrib_config)
        for ingrib in glob.glob(str(Path(driver_config["rundir"], "GRIBFILE.*")))]


def run_ungrib(config_file, cycle, key_path):

    """
    Setup and run the ungrib driver.
    """
    expt_config = get_yaml_config(config_file)
    ics_or_lbcs = "ics" if "ics" in ".".join(key_path) else "lbcs"
    external_model = expt_config["user"][ics_or_lbcs]["external_model"]

    # Run ungrib
    ungrib_driver = Ungrib(config=config_file, cycle=cycle, key_path=key_path)
    ungrib_dir = Path(ungrib_driver.config["rundir"])
    logging.info(f"Will run ungrib in {ungrib_dir}")
    if external_model == "RRFS":
        ungrib_driver.gribfiles()
        # iotaa.logcfg()
        regrid_winds(
            ungrib_driver.config,
            walk_key_path(config=expt_config, key_path=key_path)
        )
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
        key_path=args.key_path,
        )
