#!/usr/bin/env python3

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

import argparse
import datetime as dt
import glob
import logging
import os
import shutil
import subprocess
import sys
import time
import urllib.request
from copy import deepcopy
from pathlib import Path
from textwrap import dedent

import yaml

from uwtools.api.config import YAMLConfig


def clean_up_output_dir(expected_subdir, local_archive, output_path, source_paths):
    """Remove expected sub-directories and existing_archive files on
    disk once all files have been extracted and put into the specified
    output location."""

    unavailable = {}
    expand_source_paths = []
    logging.debug("Cleaning up local paths: %s", source_paths)
    for p in source_paths:
        expand_source_paths.extend(glob.glob(p.lstrip("/")))

    # Check to make sure the files exist on disk
    for file_path in expand_source_paths:
        local_file_path = str(Path.cwd() / file_path.lstrip("/"))
        logging.debug("Moving %s to %s", local_file_path, output_path)
        if not Path(local_file_path).exists():
            logging.info("File does not exist: %s", local_file_path)
            unavailable["hpss"] = expand_source_paths
        else:
            file_name = Path(file_path).name
            expected_output_loc = str(Path(output_path, file_name))
            if local_file_path != expected_output_loc:
                logging.info("Moving %s to %s", local_file_path, expected_output_loc)
                shutil.move(local_file_path, expected_output_loc)

    # Clean up directories from inside archive, if they exist
    if Path(expected_subdir).exists() and expected_subdir != "./":
        logging.info("Removing %s", expected_subdir)
        os.removedirs(expected_subdir)

    # If an archive exists on disk, remove it
    Path(local_archive).unlink(missing_ok=True)
    return unavailable


def copy_file(source, destination, copy_cmd):
    """
    Copy a file from a source and place it in the destination location.
    Return a boolean value reflecting the state of the copy.

    Assumes destination exists.
    """

    if not Path(source).exists():
        msg = "File does not exist on disk \n %s \n try using: --input_file_path <your_path>"
        logging.info(msg, source)
        return False

    # Using subprocess here because system copy is much faster than
    # python copy options.
    cmd = f"{copy_cmd} {source} {destination}"
    logging.info("Running command: \n %s", cmd)
    try:
        subprocess.run(
            cmd,
            check=True,
            shell=True,
        )
    except subprocess.CalledProcessError as err:
        logging.info(err)
        return False
    return True


def check_file(url):
    """
    Check that a file exists at the expected URL. Return boolean value
    based on the response.
    """
    status_code = urllib.request.urlopen(url).getcode()
    return status_code == 200


def download_file(url):
    """
    Download a file from a url source, and place it in a target location
    on disk.

    Arguments:
      url          url to file to be downloaded

    Return:
      boolean value reflecting state of download.

    """

    # wget flags:
    # -c continue previous attempt
    # -T timeout seconds
    # -t number of tries
    cmd = f"wget -q -c -T 15 -t 2 {url}"
    logging.debug("Running command: \n %s", cmd)
    try:
        subprocess.run(cmd, check=True, shell=True)
    except subprocess.CalledProcessError as err:
        logging.info(err)
        return False
    except:
        logging.error("Command failed!")
        raise

    return True


def _arg_list_to_range(args):
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

    args = args if isinstance(args, list) else list(args)
    arg_len = len(args)
    if arg_len in (2, 3):
        args[1] += 1
        return list(range(*args))

    return args


def _timedelta_from_str(tds: str) -> dt.timedelta:
    """
    Return a timedelta parsed from a leadtime string.

    :param tds: The timedelta string to parse.
    """
    if matches := re.match(r"(\d+)(:(\d+))?(:(\d+))?", tds):
        h, m, s = [int(matches.groups()[n] or 0) for n in (0, 2, 4)]
        return dt.timedelta(hours=h, minutes=m, seconds=s)
    _abort(f"Specify leadtime as hours[:minutes[:seconds]]")


def expand_template(template, config, cycles, lead_times, members):
    """
    Return a list of files expanded for all provided parameters.
    """
    files = []
    for cycle in cycles:
        for lead_time in lead_times:
            for member in members:
                cfg = get_yaml_config({"file": tmpl})
                cfg.dereference(
                    context={
                        "cycle": cycle,
                        "leadtime": lead_time,
                        "member": member,
                    }
                )
                files.append(cfg["file"])
    return files


def setup_logging(debug=False):
    """Calls initialization functions for logging package, and sets the
    user-defined level for logging in the script."""

    level = logging.INFO
    if debug:
        level = logging.DEBUG

    logging.basicConfig(format="%(levelname)s: %(message)s \n ", level=level)
    if debug:
        logging.info("Logging level set to DEBUG")


def write_summary_file(cla, data_store, file_templates):
    """Given the command line arguments and the data store from which
    the data was retrieved, write a bash summary file that is needed by
    the workflow elements downstream."""

    members = cla.members if isinstance(cla.members, list) else [-1]
    for mem in members:
        files = []
        for tmpl in file_templates:
            for t in tmpl if isinstance(tmpl, list) else [tmpl]:
                files.extend(
                    [fill_template(t, cla.cycle_date, fcst_hr=fh, mem=mem) for fh in cla.fcst_hrs]
                )
        output_path = fill_template(cla.output_path, cla.cycle_date, mem=mem)
        summary_fp = Path(output_path, cla.summary_file)
        logging.info("Writing a summary file to %s", summary_fp)
        file_contents = dedent(
            f"""
            DATA_SRC={data_store}
            EXTRN_MDL_CDATE={cla.cycle_date.strftime("%Y%m%d%H")}
            EXTRN_MDL_STAGING_DIR={output_path}
            EXTRN_MDL_FNS=( {" ".join(files)} )
            EXTRN_MDL_FHRS=( {" ".join([str(i) for i in cla.fcst_hrs])} )
            """
        )
        logging.info("Contents: %s", file_contents)
        summary_fp.write_text(file_contents)


def get_ens_groups(members):
    """Given a list of ensemble members, return a dict with keys for
    the ensemble group, and values are lists of ensemble members
    requested in that group."""

    if members is None:
        return {-1: [-1]}

    ens_groups: dict = {}
    for mem in members:
        ens_group = (mem - 1) // 10 + 1
        if ens_groups.get(ens_group) is None:
            ens_groups[ens_group] = [mem]
        else:
            ens_groups[ens_group].append(mem)
    return ens_groups


def parse_args(argv):
    """
    Function maintains the arguments accepted by this script. Please see
    Python's argparse documenation for more information about settings of each
    argument.
    """

    description = (
        "Allowable Python templates for paths, urls, and file names are "
        " defined in the fill_template function and include:\n"
        f"{'-' * 120}\n"
        f"{fill_template('null', dt.datetime.now(tz=dt.timezone.utc), templates_only=True)}"
    )
    parser = argparse.ArgumentParser(
        description=description,
    )

    # Required
    parser.add_argument(
        "--file_set",
        choices=("anl", "fcst", "obs", "fix"),
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
        help="The cycle in ISO8601 format (e.g. %s)" % cycle.strftime("%Y-%m-%dT%H"),
        required=False,
        default=dt.datetime.now(),
        type=dt.datetime.fromisoformat,
    )
    parser.add_argument(
        "--data_stores",
        choices=["hpss", "nomads", "aws", "disk"],
        help="List of priority data_stores. Tries first list item first.",
        nargs="*",
        required=True,
        type=to_lower,
    )
    parser.add_argument(
        "--data_type",
        help="External model label. This input is case-sensitive",
        required=True,
    )
    parser.add_argument(
        "--fcst_hrs",
        help="A list describing forecast hours.  If one argument, \
        one fhr will be processed.  If 2 or 3 arguments, a sequence \
        of forecast hours [start, stop, [increment]] will be \
        processed.  If more than 3 arguments, the list is processed \
        as-is. default=[0]",
        nargs="+",
        required=False,
        default=[0],
        type=lambda x: [_timedelta_from_str(t) for t in _arg_list_to_range(x)],
    )
    parser.add_argument(
        "--output_path",
        help="Path to a location on disk. Path is expected to exist.",
        required=True,
        type=os.path.abspath,
    )
    parser.add_argument(
        "--ics_or_lbcs",
        choices=("ICS", "LBCS"),
        help="Flag for whether ICS or LBCS.",
        required=False,
    )

    # Optional
    parser.add_argument(
        "--version",
        help="Version number of package to download, e.g. x.yy.zz",
    )
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
        "--file_templates",
        help="One or more file template strings defining the naming \
        convention to be used for the files retrieved from disk. If \
        not provided, the default names from hpss are used.",
        nargs="*",
    )
    parser.add_argument(
        "--file_fmt",
        choices=("grib2", "nemsio", "netcdf", "prepbufr", "tcvitals"),
        help="External model file format",
    )
    parser.add_argument(
        "--input_file_path",
        help="A path to data stored on disk. The path may contain \
        Python templates. File names may be supplied using the \
        --file_templates flag, or the default naming convention will be \
        taken from the --config file.",
    )
    parser.add_argument(
        "--members",
        help="A list describing ensemble members.  If one argument, \
        one member will be processed.  If 2 or 3 arguments, a sequence \
        of members [start, stop, [increment]] will be \
        processed.  If more than 3 arguments, the list is processed \
        as-is.",
        nargs="*",
        type=_arg_list_to_range,
    )
    parser.add_argument(
        "--summary_file",
        help="Name of the summary file to be written to the output \
        directory",
    )
    parser.add_argument(
        "--check_file",
        action="store_true",
        help="Use this flag to check the existence of requested files, \
         but don't try to download them. Works with download protocol \
         only",
    )

    # Make modifications/checks for given values
    args = parser.parse_args(argv)

    # Check required arguments for various conditions
    if not args.ics_or_lbcs and args.file_set in ["anl", "fcst"]:
        msg = f"--ics_or_lbcs is a required argument when --file_set = {args.file_set}"
        raise argparse.ArgumentTypeError(msg)

    # If disk was in data_stores, make sure a path was provided
    if "disk" in args.data_stores:
        # Make sure a path was provided.
        if not args.input_file_path:
            raise argparse.ArgumentTypeError(
                ("You must provide an input_file_path when choosing  disk as a data store!")
            )

    # Ensure hpss module is loaded if hpss is included in data stores
    if "hpss" in cla.data_stores:
        try:
            subprocess.run(
                "which hsi",
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


def retrieve_data(
    cycle: datetime,
    data_stores: list,
    data_type: str,
    file_set: str,
    config: Optional[YAMLConfig],
    check_file: bool = False,
    file_fmt: Optional[str] = None,
    fcst_hrs: Optional[list] = None,
    file_templates: Optional[list] = None,
    ics_or_lbcs: Optional[str] = None,
    input_file_path: Optional[str] = None,
    members: Optional[list[int]] = None,
    summary_file: Optional[str, Path] = None,
) -> bool:
    """
    Checks for and gathers the requested data.
    """

    for store in data_stores:
        args = {
            "data_store": store,
            "cycle": cyle,
            "lead_times": fcst_hrs,
            "members": members,
        }
        if store == "disk":
            args.update(
                {
                    "file_path": input_file_path,
                    "file_templates": input_file_templates,
                }
            )
        else:
            args.update(
                {
                    "config": config[data_type][store],
                    "file_set": file_set,
                    "file_format": file_fmt,
                }
            )
        success = try_data_store(**args)


def try_data_store(
    data_store: str,
    cycle: dt.datetime,
    lead_times: list[dt.timedelta],
    members: Optional[list[str]] = None,
    file_path: Optional[Path] = None,
    file_templates: Optional[list[str]] = None,
    config: Optional[YAMLConfig] = None,
    file_set: Optional[str] = None,
    file_format: Optional[str] = None,
):
    """
    Given a data store, prepare a UW YAML file block to retrieve all requested
    data. Iterate through each potential option until the data set is retrieved.
    """
    # check for correct data_store
    if data_store == "disk":
        assert file_path is not None
        assert file_templates is not None

    # form a UW YAML to try a copy

    return False


def main(args):
    clargs = parse_args(args)

    setup_logging(debug)
    print("Running script retrieve_data.py with args:", f"\n{('-' * 80)}\n{('-' * 80)}")
    for name, val in cla.__dict__.items():
        if name not in ["config"]:
            print(f"{name:>15s}: {val}")
    print(f"{('-' * 80)}\n{('-' * 80)}")

    retrieve_data(
        config=clargs.config,
        cycle=clargs.cycle,
        data_stores=clargs.data_stores,
        data_type=clargs.data_type,
        file_set=clargs.file_set,
        check_file=clargs.check_file,
        file_fmt=clargs.file_fmt,
        lead_times=clargs.lead_times,
        file_templates=clargs.file_templates,
        ics_or_lbcs=clargs.ics_or_lbcs,
        input_file_path=clargs.input_file_path,
        members=clargs.members,
        summary_file=clargs.summary_file,
    )


if __name__ == "__main__":
    main(sys.argv[1:])
