#!/usr/bin/env python3
"""
The runscript for UPP.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from uwtools.api.upp import UPP

from scripts.common import parse_args, run_component


def main():
    args = parse_args(lead_required=True)
    run_component(
        driver_class=UPP,
        config_file=args.config_file,
        cycle=args.cycle,
        leadtime=args.leadtime,
        key_path=args.key_path,
    )


if __name__ == "__main__":
    main()  # pragma: no cover
