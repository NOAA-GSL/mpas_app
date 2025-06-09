#!/usr/bin/env python3
"""
The run script for the MPAS init_atmosphere.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from uwtools.api.mpas_init import MPASInit

from scripts.common import parse_args, run_component


def main():
    args = parse_args()
    run_component(
        driver_class=MPASInit,
        config_file=args.config_file,
        cycle=args.cycle,
        key_path=args.key_path,
    )


if __name__ == "__main__":
    main()  # pragma: no cover
