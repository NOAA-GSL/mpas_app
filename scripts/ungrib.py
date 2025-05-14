#!/usr/bin/env python3
"""
The run script for ungrib.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from uwtools.api.ungrib import Ungrib

from scripts.common import parse_args, run_component


def main():
    args = parse_args()
    run_component(
        driver_class=Ungrib,
        config_file=args.config_file,
        cycle=args.cycle,
        key_path=args.key_path,
    )


if __name__ == "__main__":
    main()  # pragma: no cover
