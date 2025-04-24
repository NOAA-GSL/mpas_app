#!/usr/bin/env python3

"""
The runscript for UPP.
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

from uwtools.api.upp import UPP


def main():
    # Load the YAML config
    config_path = os.environ["CONFIG_PATH"]
    lead = timedelta(hours=int(os.environ["LEAD"]))
    cycle = datetime.fromisoformat(os.environ["CYCLE"])

    # Run UPP
    upp_driver = UPP(config=config_path, cycle=cycle, leadtime=lead, key_path=["post"])
    upp_driver.run()

    # Obtain run directory path
    upp_dir = Path(upp_driver.config["rundir"])

    if not (upp_dir / "runscript.upp.done").is_file():
        print("Error occurred running UPP. Please see component error logs.")
        sys.exit(1)


if __name__ == "__main__":
    main()
