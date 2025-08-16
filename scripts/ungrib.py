#!/usr/bin/env python3
"""
The run script for ungrib.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from iotaa import asset, external, task, tasks
from uwtools.api.config import get_yaml_config, YAMLConfig
from uwtools.api.logging import use_uwtools_logger
from uwtools.api.ungrib import Ungrib

from scripts.common import parse_args
from scripts.utils import run_shell_cmd, walk_key_path


@external
def file(path: Path):
    yield f"{path}"
    yield asset(path, path.is_file)


@task
def regrid_input(driver: Ungrib, infile: Path, wgrib_config: dict):
    """
    Use wgrib2 to regrid the input file winds.

    :param infile: Input file path.
    :param wgrib_config: User-provided configuration settings.
    """
    taskname = f"wgrib2 regrid {infile}"
    yield taskname
    outfile = driver.rundir / f"tmp.{infile.name}.grib2"
    yield asset(outfile, outfile.is_file)
    yield driver.gribfiles()
    gribfile = infile.resolve()
    # Removes the GRIBFILE.* link.
    infile.unlink()
    budget_fields = Path(wgrib_config["budget_fields"]).read_text().strip()
    neighbor_fields = Path(wgrib_config["neighbor_fields"]).read_text().strip()
    # MUST leave space after {neighbor_fields} below for now.
    options = [
        "-set_bitmap 1",
        "-set_grib_type c3",
        "-new_grid_winds grid",
        f"-new_grid_vectors {wgrib_config['grid_vectors']}",
        "-new_grid_interpolation bilinear",
        f"-if '{budget_fields}' -new_grid_interpolation budget -fi",
        # DO NOT REMOVE SPACE   v
        f"-if '{neighbor_fields} ' -new_grid_interpolation neighbor -fi",
        f"-new_grid {wgrib_config['grid_specs']}",
    ]
    cmd = f"""
    module load wgrib2
    wgrib2 {gribfile} {" ".join(options)} {outfile}
    """
    run_shell_cmd(
        cmd=cmd,
        cwd=driver.rundir,
        log_output=True,
        taskname=taskname,
    )


@task
def merge_vector_fields(driver: Ungrib, infile: Path, wgrib_config: dict):
    """
    Use wgrib2 to merge vector fields.
    """
    taskname = f"wgrib2 merge vector fields {infile}"
    yield taskname
    outfile = driver.rundir / f"tmp2.{infile.name}.grib2"
    yield asset(outfile, outfile.is_file)
    regrid_task = regrid_input(driver, infile, wgrib_config)
    yield regrid_task
    options = [
        "-not aerosol=Dust",
        f"-new_grid_vectors {wgrib_config['grid_vectors']}",
        "-submsg_uv",
    ]
    cmd = f"""
    module load wgrib2
    wgrib2 {regrid_task.ref} {" ".join(options)} {outfile}
    """
    success, log = run_shell_cmd(
        cmd=cmd,
        cwd=driver.rundir,
        log_output=True,
        taskname=taskname,
    )
    if success:
        infile.symlink_to(outfile)
    else:
        for line in log.split("\n"):
            logging.error(line)
        outfile.unlink()


@tasks
def regrid_all(driver: Ungrib, wgrib2_config: dict):
    """
    Use wgrib2 to regrid the winds.
    """
    yield "Regridding winds with wgrib2"
    gribfiles = driver.gribfiles()
    yield [merge_vector_fields(driver, ingrib, wgrib2_config) for ingrib in gribfiles.ref]


@task
def run_ungrib(config_file, cycle, key_path):
    """
    Setup and run the ungrib driver.
    """
    expt_config = get_yaml_config(config_file)
    expt_config.dereference(context={**expt_config, "cycle": cycle})
    ics_or_lbcs = "ics" if "ics" in ".".join(key_path) else "lbcs"
    external_model = expt_config["user"][ics_or_lbcs]["external_model"]
    yield f"run ungrib for {external_model} {ics_or_lbcs}"
    ungrib_block = walk_key_path(config=expt_config, key_path=key_path)
    rundir = Path(ungrib_block["ungrib"]["rundir"]).parent / external_model
    summary = get_yaml_config(rundir / "ICS.yaml")
    gribfiles = [Path(rundir, p) for p in summary.keys()]
    if ics_or_lbcs == "lbcs":
        lbcs_summary = get_yaml_config(rundir / "LBCS.yaml")
        gribfiles.extend(Path(rundir, p) for p in lbcs_summary.keys())
    ungrib_block["ungrib"]["gribfiles"] = [str(p) for p in gribfiles]
    driver = Ungrib(config=expt_config, cycle=cycle, key_path=key_path)
    yield [asset(x, x.is_file) for x in driver.output["paths"]]
    yield (
        regrid_all(driver, walk_key_path(config=expt_config, key_path=key_path)["wgrib2"])
        if external_model == "RRFS"
        else None
    )
    # Run ungrib.
    logging.info("Running %s in %s", Ungrib.__name__, driver.rundir)
    driver.run()


def main():
    args = parse_args()
    use_uwtools_logger()
    if not run_ungrib(
        config_file=args.config_file,
        cycle=args.cycle,
        key_path=args.key_path,
    ).ready:
        print("Error occurred running ungrib. Please see component error logs.")
        sys.exit(1)


if __name__ == "__main__":
    main()  # pragma: no cover
