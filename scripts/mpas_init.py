#!/usr/bin/env python3
"""
The run script for the MPAS init_atmosphere.
"""

import inspect
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from uwtools.api.config import get_yaml_config
from uwtools.api.mpas_init import MPASInit

from scripts.common import parse_args, run_component
from scripts.utils import run_shell_cmd


def variables_from_fix(expt_config, driver_config):
    """
    Call ncks for variables that should come from fix files
    """
    init_file = driver_config["streams"]["output"]["filename_template"]
    files_to_link = driver_config["files_to_link"]
    mesh_label = expt_config["user"]["mesh_label"]
    for variable in ("shdmax", "shdmin"):
        fix_file = files_to_link[f"{variable}.{mesh_label}.nc"]
        cmd = f"module load nco ; ncks -A -v {variable} {fix_file} {init_file}"
        run_shell_cmd(
            cmd=cmd,
            cwd=driver_config["rundir"],
            log_output=True,
            taskname=inspect.stack()[0][3],
        )


def main():
    args = parse_args()
    mpas_init_driver = run_component(
        driver_class=MPASInit,
        config_file=args.config_file,
        cycle=args.cycle,
        key_path=args.key_path,
    )
    # For RRFS ICS, use some variables from fix files
    expt_config = get_yaml_config(args.config_file)
    external_model = expt_config["user"]["ics"]["external_model"]
    if external_model == "RRFS" and "ics" in args.key_path:
        variables_from_fix(expt_config, mpas_init_driver.config)


if __name__ == "__main__":
    main()  # pragma: no cover
