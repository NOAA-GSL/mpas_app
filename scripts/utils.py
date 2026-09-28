from __future__ import annotations

import sys

from uwtools.logging import log


def walk_key_path(config, key_path):
    """
    Navigate to the sub-config at the end of the path of given keys.
    """
    keys = []
    pathstr = "<unknown>"
    for key in key_path:
        keys.append(key)
        pathstr = " -> ".join(keys)
        try:
            subconfig = config[key]
        except KeyError:
            log.error("Bad config path: %s", pathstr)
            raise
        if not isinstance(subconfig, dict):
            log.error("Value at %s must be a dictionary", pathstr)
            sys.exit(1)
        config = subconfig
    return config
