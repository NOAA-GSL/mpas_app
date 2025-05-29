#!/usr/bin/env python3


# Ignore PLR0913 Too many arguments in function definition
# ruff: noqa: PLR0913

"""
This script helps users pull data from known data streams, including
URLS and HPSS (only on supported NOAA platforms), or from user-supplied
data locations on disk.

Several supported data streams are included in
parm/data_locations.yml, which provides locations and naming
conventions for files commonly used with the SRW App. Provide the file
to this tool via the --config flag. Users are welcome to provide their
own file with alternative locations and naming conventions.

When using this script to pull from disk, the user is required to
provide the path to the data location, which can include Python
templates. The file names follow those included in the --config file by
default, or can be user-supplied via the --file_name flag. That flag
takes a YAML-formatted string that follows the same conventions outlined
in the parm/data_locations.yml file for naming files.

To see usage for this script:

    python retrieve_data.py -h

Also see the parse_args function below.
"""

from __future__ import annotations

import argparse
import logging
import re
import subprocess
import sys
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any, NoReturn

from uwtools.api import fs
from uwtools.api.config import Config, YAMLConfig, get_yaml_config
from uwtools.api.logging import use_uwtools_logger

if TYPE_CHECKING:
    from collections.abc import Generator

FILE_SETS = ("anl", "fcst", "obs", "fix")


def _abort(msg: str) -> NoReturn:
    """
    Exit with an informative message and error status.

    :param msg: The message to print.
    """
    print(msg, file=sys.stderr)
    sys.exit(1)


def _arg_list_to_range(args: list[int | str] | str) -> list:
    """
    Given an argparse list argument, return the sequence to process.

    The length of the list will determine what sequence items are returned:

      Length = 1:   A single item is to be processed
      Length = 2:   A sequence of start, stop with increment 1
      Length = 3:   A sequence of start, stop, increment
      Length > 3:   List as is

    argparse should provide a list of at least one item (nargs='+').

    Must ensure that the list contains integers.
    """

    arg_list = args.split(" ") if isinstance(args, str) else args
    arg_vals = [int(i) for i in arg_list]
    arg_len = len(arg_vals)
    if arg_len in (2, 3):
        arg_vals[1] += 1
        return list(range(*arg_vals))

    return arg_vals


def _timedelta_from_str(tds: str) -> timedelta:
    """
    Return a timedelta parsed from a leadtime string.

    :param tds: The timedelta string to parse.
    """
    if matches := re.match(r"(\d+)(:(\d+))?(:(\d+))?", tds):
        h, m, s = [int(matches.groups()[n] or 0) for n in (0, 2, 4)]
        return timedelta(hours=h, minutes=m, seconds=s)
    _abort("Specify leadtime as hours[:minutes[:seconds]]")


def parse_args(argv):
    """
    Function maintains the arguments accepted by this script. Please see
    Python's argparse documenation for more information about settings of each
    argument.
    """

    parser = argparse.ArgumentParser()

    # Required
    parser.add_argument(
        "--file-set",
        choices=FILE_SETS,
        help="Flag for whether analysis, forecast, \
        fix, or observation files should be gathered",
        required=True,
    )
    parser.add_argument(
        "--config",
        help="Full path to a configuration file containing paths and \
        naming conventions for known data streams. The default included \
        in this repository is in parm/data_locations.yml",
        required=False,
        type=get_yaml_config,
    )
    parser.add_argument(
        "--cycle",
        help="The cycle in ISO8601 format (e.g. yyyy-mm-ddThh)",
        required=False,
        default=datetime.now(tz=timezone.utc),
        type=lambda x: datetime.fromisoformat(x).replace(tzinfo=timezone.utc),
    )
    parser.add_argument(
        "--data-stores",
        choices=["hpss", "nomads", "aws", "disk"],
        help="List of priority data_stores. Tries first list item first.",
        nargs="*",
        required=True,
    )
    parser.add_argument(
        "--data-type",
        help="External model label. This input is case-sensitive",
        required=True,
    )
    parser.add_argument(
        "--fcst-hrs",
        help="A list describing forecast hours.  If one argument, \
        one fhr will be processed.  If 2 or 3 arguments, a sequence \
        of forecast hours [start, stop, [increment]] will be \
        processed.  If more than 3 arguments, the list is processed \
        as-is. default=[0]",
        nargs="+",
        required=False,
        default=[0],
        type=int,
    )
    parser.add_argument(
        "--output-path",
        help="Path to a location on disk. Path is expected to exist.",
        required=True,
        type=lambda x: Path(x).resolve(),
    )

    # Optional
    parser.add_argument(
        "--symlink",
        action="store_true",
        help="Symlink data files when source is disk",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Print debug messages",
    )
    parser.add_argument(
        "--file-templates",
        help="One or more file template strings defining the naming \
        convention to be used for the files retrieved from disk. If \
        not provided, the default names from hpss are used.",
        nargs="*",
        default=[],
    )
    parser.add_argument(
        "--file-fmt",
        choices=("grib2", "nemsio", "netcdf", "prepbufr", "tcvitals"),
        help="External model file format",
    )
    parser.add_argument(
        "--input-file-path",
        help="A path to data stored on disk. The path may contain \
        Python templates. File names may be supplied using the \
        --file_templates flag, or the default naming convention will be \
        taken from the --config file.",
        type=Path,
    )
    parser.add_argument(
        "--members",
        help="A list describing ensemble members.  If one argument, \
        one member will be processed.  If 2 or 3 arguments, a sequence \
        of members [start, stop, [increment]] will be \
        processed.  If more than 3 arguments, the list is processed \
        as-is.",
        nargs="*",
        type=int,
        default=[-999],
    )
    parser.add_argument(
        "--summary-file",
        help="Name of the summary file to be written to the output \
        directory",
        type=Path,
    )

    # Make modifications/checks for given values
    args = parser.parse_args(argv)
    args.fcst_hrs = [_timedelta_from_str(str(t)) for t in _arg_list_to_range(args.fcst_hrs)]
    args.members = _arg_list_to_range(args.members)
    # Check required arguments for various conditions

    # If disk was in data_stores, make sure a path was provided
    if "disk" in args.data_stores and not args.input_file_path:
        msg = "You must provide an input_file_path when choosing  disk as a data store!"
        raise argparse.ArgumentTypeError(msg)

    # Ensure hpss module is loaded if hpss is included in data stores
    if "hpss" in args.data_stores:
        try:
            subprocess.run(
                "/usr/bin/which hsi",
                check=True,
                shell=True,
            )
        except subprocess.CalledProcessError:
            logging.error(
                "You requested the hpss data store, but "
                "the HPSS module isn't loaded. This data store "
                "is only available on NOAA compute platforms."
            )
            sys.exit(1)
    return args


def get_file_names(
    file_name_config: dict[str, Any],
    file_fmt: str | None,
    file_set: str,
) -> Any:
    files = file_name_config.get(file_set, [])
    return files.get(file_fmt or "", []) if isinstance(files, dict) else files


def retrieve_data(
    config: YAMLConfig,
    cycle: datetime,
    data_stores: list[str],
    data_type: str,
    file_set: str,
    outpath: Path,
    file_templates: list[str],
    lead_times: list[timedelta],
    members: list[int],
    file_fmt: str | None = None,
    inpath: Path | None = None,
    summary_file: str | Path | None = None,
    *,
    symlink: bool = False,
) -> bool:
    """
    Checks for and gathers the requested data.
    """

    standard_file_names = get_file_names(config[data_type]["file_names"], file_fmt, file_set)
    config.dereference(context={"cycle": cycle})
    for store in data_stores:
        # checks for given data_store
        if store == "disk":
            assert inpath is not None
        else:
            assert config
            assert file_set in FILE_SETS

        archive_names = None
        if store == "hpss":
            archive_names = config[data_type][store]["archive_file_names"]
            if isinstance(archive_names, dict):
                archive_names = get_file_names(archive_names, file_fmt, file_set)

        store_file_names = []
        if store != "disk" and (fns := config[data_type][store].get("file_names")):
            store_file_names = get_file_names(fns, file_fmt, file_set)

        success, files_copied = try_data_store(
            data_store=store,
            config=config,
            cycle=cycle,
            file_templates=file_templates
            if all(file_templates) and store == "disk"
            else store_file_names or standard_file_names,
            lead_times=lead_times,
            locations=[inpath]
            if inpath and store == "disk"
            else config[data_type][store]["locations"],
            members=members,
            outpath=outpath,
            archive_config=config[data_type][store] if store == "hpss" else None,
            archive_names=archive_names,
            symlink=symlink,
        )
        if success:
            if summary_file is not None:
                summary = get_yaml_config(files_copied)
                summary.dump(Path(summary_file))
            return success
    return success


def possible_hpss_configs(
    archive_locations: dict[str, str],
    archive_names: list[str],
    config: Config,
    cycle: datetime,
    file_templates: list[str],
    lead_times: list[timedelta],
    members: list[int],
):
    for archive_loc in archive_locations["locations"]:
        for internal_dir in archive_locations["archive_internal_dirs"]:
            for archive_name in archive_names:
                location = f"htar://{archive_loc}/{archive_name}?{internal_dir}"
                fs_copy_config: dict[str, str] = {}
                for member in members:
                    for lead_time in lead_times:
                        for file_template in file_templates:
                            # Don't path join the next line because location won't be a path on disk
                            local_name = (
                                f"mem{member:03d}/{file_template}"
                                if member != -999
                                else file_template
                            )
                            file_item = get_yaml_config({local_name: f"{location}/{file_template}"})
                            context = {
                                "cycle": cycle,
                                "lead_time": lead_time,
                                "mem": member,
                            }
                            file_item.dereference(
                                context={
                                    **context,
                                    **deepcopy(config).dereference(
                                        context=context,
                                    ),
                                }
                            )
                            fs_copy_config.update(file_item)
                yield fs_copy_config


def prepare_fs_copy_config(
    config: Config,
    cycle: datetime,
    file_templates: list[str],
    lead_times: list[timedelta],
    locations: list[list | Path | str],
    members: list[int],
) -> Generator[dict[str, str]]:
    fs_copy_config: dict[str, str] = {}
    for location in locations:
        for member in members:
            for lead_time in lead_times:
                # Don't path join because location can be a url
                mem_prefix = f"mem{member:03d}/" if member != -999 else ""
                if isinstance(location, list):
                    if isinstance(file_templates, list) and len(file_templates) == len(location):
                        file_item = get_yaml_config(
                            {
                                f"{mem_prefix}{fn}": f"{loc}/{fn}"
                                for loc, fn in zip(location, file_templates)
                            }
                        )
                else:
                    file_item = get_yaml_config(
                        {f"{mem_prefix}{fn}": f"{location}/{fn}" for fn in file_templates}
                    )
                context = {
                    "cycle": cycle,
                    "lead_time": lead_time,
                    "mem": member,
                }
                file_item.dereference(
                    context={
                        **context,
                        **deepcopy(config).dereference(
                            context=context,
                        ),
                    }
                )
                fs_copy_config.update(file_item)
        yield fs_copy_config


def try_data_store(
    config: Config,
    cycle: datetime,
    data_store: str,
    file_templates: list[str],
    lead_times: list[timedelta],
    locations: list[list | Path | str],
    members: list[int],
    outpath: Path,
    archive_config: dict[str, str] | None = None,
    archive_names: list[str] | None = None,
    *,
    symlink: bool = False,
) -> tuple[bool, dict[str, str]]:
    """
    Given a data store, prepare a UW YAML file block to retrieve all requested
    data. Iterate through each potential option until the data set is retrieved.
    """

    # form a UW YAML to try a copy
    fs_copy_configs: Generator[dict[str, str], None, None]
    if data_store == "hpss":
        assert archive_config is not None
        assert archive_names is not None
        fs_copy_configs = possible_hpss_configs(
            archive_locations=archive_config,
            archive_names=archive_names,
            config=config,
            cycle=cycle,
            file_templates=file_templates,
            lead_times=lead_times,
            members=members,
        )
    else:
        fs_copy_configs = prepare_fs_copy_config(
            config=config,
            cycle=cycle,
            file_templates=file_templates,
            lead_times=lead_times,
            locations=locations,
            members=members,
        )
    for fs_copy_config in fs_copy_configs:
        getter = fs.link if symlink else fs.copy
        files_copied = getter(config=fs_copy_config, target_dir=outpath, cycle=cycle)
        if files_copied["ready"] and not files_copied["not-ready"]:
            logging.info(files_copied)
            return True, fs_copy_config

    return False, {}


def main(args):
    clargs = parse_args(args)

    use_uwtools_logger(verbose=clargs.debug)
    print("Running script retrieve_data.py with args:", f"\n{('-' * 80)}\n{('-' * 80)}")
    for name, val in clargs.__dict__.items():
        if name not in ["config"]:
            print(f"{name:>15s}: {val}")
    print(f"{('-' * 80)}\n{('-' * 80)}")

    retrieve_data(
        config=clargs.config,
        cycle=clargs.cycle,
        data_stores=clargs.data_stores,
        data_type=clargs.data_type,
        file_set=clargs.file_set,
        file_fmt=clargs.file_fmt,
        lead_times=clargs.fcst_hrs,
        file_templates=clargs.file_templates,
        inpath=clargs.input_file_path,
        members=clargs.members,
        outpath=clargs.output_path,
        summary_file=clargs.summary_file,
        symlink=clargs.symlink,
    )


if __name__ == "__main__":
    main(sys.argv[1:])  # pragma: no cover
