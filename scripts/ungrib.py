#!/usr/bin/env python3
"""
The run script for ungrib.
"""

import glob
import inspect
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from iotaa import asset, external, task, tasks, refs
from uwtools.api.ungrib import Ungrib
from uwtools.api.config import get_yaml_config

from scripts.common import parse_args, run_component
from scripts.utils import run_shell_cmd, walk_key_path

@external
def file(path: Path):
    yield f"{path}"
    yield asset(path, path.is_file)

@task
def regrid_input(infile: Path, rundir, wgrib_config: dict):
    """
    Use wgrib2 to regrid the input file winds.

    :param infile: Input file path.
    :param wgrib_config: User-provided configuration settings.
    """
    outfile = Path(rundir, infile.resolve().stem + ".tmp.grib2")
    yield f"wgrib2 regrid {outfile}"
    yield asset(outfile, outfile.is_file)
    yield file(infile)
    budget_fields = Path(wgrib_config["budget_fields"]).read_text().strip()
    neighbor_fields = Path(wgrib_config["neighbor_fields"]).read_text().strip()
    # MUST leave space after {neighbor_fields} below for now.
    options = [
        "-set_bitmap 1",
        "-set_grib_type c3",
        "-new_grid_winds grid",
        f"-new_grid_vectors {wgrib_config['grid_vectors']}",
        "-new_grid_interpolation bilinear",
        f"-if \'{budget_fields}\' -new_grid_interpolation budget -fi",
        # DO NOT REMOVE SPACE    v
        f"-if \'{neighbor_fields} \' -new_grid_interpolation neighbor -fi",
        f"-new_grid {wgrib_config['grid_specs']}",
        ]
    cmd = f"""
    module load wgrib2
    wgrib2 {infile} {" ".join(options)} {outfile}"""
    run_shell_cmd(
        cmd=cmd,
        cwd=rundir,
        env={},
        log_output=True,
        taskname=inspect.stack()[0][3],
        )

@task
def merge_vector_fields(infile: Path, outfile: Path, rundir: Path, wgrib_config: dict):
    """
    Use wgrib2 to merge vector fields.
    """
    yield f"wgrib2 merge vector fields {outfile}"
    yield asset(outfile, outfile.is_file)
    regrid_task = regrid_input(infile, rundir, wgrib_config)
    yield regrid_task
    # or refs(regrid_task)
    # iotaa.logcfg -- for iotaa output logging.

    cmd = f"""
    module load wgrib2
    wgrib2 {refs(regrid_task)} -not aerosol=Dust -new_grid_vectors \"{wgrib_config['grid_vectors']}\" -submsg_uv {outfile}
       """
    run_shell_cmd(
        cmd=cmd,
        cwd=rundir,
        log_output=True,
        taskname=inspect.stack()[0][3],
        )

@task
def link_to_regridded_grib(infile:Path, rundir: Path, wgrib_config: dict):
    """
    Update original link to point to regridded grib file.
    """
    linked_file = infile.resolve()
    outfile = linked_file.name if "tmp" in linked_file.name else linked_file.stem + ".tmp2.grib2"
    yield f"ungrib: update link {infile} to {outfile}"
    yield asset(infile, lambda: infile.resolve().name == outfile)
    yield merge_vector_fields(infile, Path(rundir, outfile), rundir, wgrib_config)
    infile.unlink()
    infile.symlink_to(outfile)

@tasks
def regrid_winds(rundir:Path, task_config: dict):
    """
    Use wgrib2 to regrid the winds.
    """
    wgrib_config = task_config["wgrib2"]
    yield "Regridding winds with wgrib2"
    yield [link_to_regridded_grib(Path(ingrib), rundir, wgrib_config)
        for ingrib in glob.glob(str(Path(rundir, "GRIBFILE.*")))]


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
        regrid_winds(
            ungrib_driver.config["rundir"],
            walk_key_path(config=expt_config, key_path=key_path)
        )
    ungrib_driver.run()

    if not (ungrib_dir / "runscript.ungrib.done").is_file():
        print("Error occurred running ungrib. Please see component error logs.")
        sys.exit(1)


def main():
    args = parse_args()
    run_ungrib(
        config_file=args.config_file,
        cycle=args.cycle,
        key_path=args.key_path,
    )


if __name__ == "__main__":
    main()  # pragma: no cover
