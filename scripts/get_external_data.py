#!/usr/bin/env python3
"""
Setup for calling retrieve_data.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from uwtools.api.config import get_yaml_config
from uwtools.api.logging import use_uwtools_logger

from scripts.common import parse_args
from scripts.utils import walk_key_path
from ush.retrieve_data import _abort, _arg_list_to_range, _timedelta_from_str, retrieve_data


def main():
    args = parse_args()
    use_uwtools_logger()
    expt_config = get_yaml_config(args.config_file)
    expt_config.dereference(context={"cycle": args.cycle})
    data_config = walk_key_path(config=expt_config, key_path=args.key_path)

    lead_times = [
        _timedelta_from_str(str(t))
        for t in _arg_list_to_range(data_config["config"].pop("lead_times"))
    ]
    if not retrieve_data(
        config=get_yaml_config(data_config["config"].pop("config")),
        cycle=args.cycle,
        lead_times=lead_times,
        members=[-999],
        **data_config["config"],
    ):
        _abort("Files were not staged!")


if __name__ == "__main__":
    main()  # pragma: no cover
