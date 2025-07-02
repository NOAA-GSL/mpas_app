from __future__ import annotations

import sys
from subprocess import STDOUT, CalledProcessError, check_output
from typing import TYPE_CHECKING

from uwtools.logging import INDENT, log

if TYPE_CHECKING:
    from pathlib import Path

def run_shell_cmd(
    cmd: str,
    cwd: Path | str | None = None,
    env: dict[str, str] | None = None,
    log_output: bool | None = False,
    taskname: str | None = None,
) -> tuple[bool, str]:
    """
    Run a command in a shell.

    :param cmd: The command to run.
    :param cwd: Change to this directory before running cmd.
    :param env: Environment variables to set before running cmd.
    :param log_output: Log output from successful cmd? (Error output is always logged.)
    :param taskname: Name of task executing this command, for logging.
    :return: A result object providing combined stderr/stdout output and success values.
    """
    pre = f"{taskname}: " if taskname else ""
    msg = f"%sRunning: {cmd}"
    if cwd:
        msg += f" in {cwd}"
    if env:
        kvpairs = " ".join(f"{k}={v}" for k, v in env.items())
        msg += f" with environment variables {kvpairs}"
    log.info(msg, pre)
    try:
        output = check_output(
            cmd, cwd=cwd, encoding="utf=8", env=env, shell=True, stderr=STDOUT, text=True
        )
        logfunc = log.info
        success = True
    except CalledProcessError as e:
        output = e.output
        log.error("%sFailed with status: %s", pre, e.returncode)
        logfunc = log.error
        success = False
    if output and (log_output or not success):
        logfunc("%sOutput:", pre)
        for line in output.split("\n"):
            logfunc("%s%s%s", pre, INDENT, line)
    return success, output

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
