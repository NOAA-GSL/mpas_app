import sys
from subprocess import CalledProcessError
from unittest.mock import patch

import pytest

from scripts import utils


def test_walk_key_path_fail_bad_key_path():
    config = {"a": {"b": {"c": "cherry"}}}
    with pytest.raises(KeyError):
        utils.walk_key_path(config, ["a", "x"])


def test_walk_key_path_fail_bad_leaf_value():
    config = {"a": {"b": {"c": "cherry"}}}
    with pytest.MonkeyPatch().context() as m:
        m.setattr(sys, "exit", lambda code: (_ for _ in ()).throw(SystemExit(code)))
        with pytest.raises(SystemExit) as e:
            utils.walk_key_path(config, ["a", "b", "c"])
        assert e.type is SystemExit
        assert e.value.code == 1


def test_walk_key_path_pass():
    config = {"a": {"b": {"c": "cherry"}}}
    expected = {"c": "cherry"}
    assert utils.walk_key_path(config, ["a", "b"]) == expected


def test_run_shell_cmd__failure(caplog):
    cmd = "expr 1 / 0"
    with (
        patch(
            "scripts.utils.check_output",
            side_effect=CalledProcessError(2, cmd, output="expr: division by zero"),
        ),
        patch("scripts.utils.INDENT", "  "),
        caplog.at_level("INFO"),
    ):
        success, output = utils.run_shell_cmd(cmd=cmd)
    assert not success
    assert "division by zero" in output
    logs = caplog.text
    assert "Running: expr 1 / 0" in logs
    assert "Failed with status: 2" in logs
    assert "Output:" in logs
    assert "expr: division by zero" in logs


def test_run_shell_cmd__success(tmp_path, caplog):
    cmd = "echo hello $FOO"
    with (
        patch("scripts.utils.check_output", return_value="hello bar"),
        patch("scripts.utils.INDENT", "  "),
        caplog.at_level("INFO"),
    ):
        success, output = utils.run_shell_cmd(
            cmd=cmd, cwd=tmp_path, env={"FOO": "bar"}, log_output=True
        )
    assert success
    assert "hello bar" in output
    logs = caplog.text
    assert f"Running: {cmd} in {tmp_path}" in logs
    assert "FOO=bar" in logs
    assert "Output:" in logs
    assert "hello bar" in logs
