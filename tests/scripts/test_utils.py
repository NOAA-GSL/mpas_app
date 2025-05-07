import pytest

from scripts import utils


def test_run_shell_cmd(tmp_path, caplog):
    caplog.set_level("INFO")
    cmd = "echo hello $FOO"
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


def test_run_shell_cmd_failure(caplog):
    caplog.set_level("INFO")
    cmd = "expr 1 / 0"
    success, output = utils.run_shell_cmd(cmd=cmd)
    assert success is False
    assert "division by zero" in output
    logs = caplog.text
    assert ("Running: %s" % cmd) in logs
    assert "Failed with status: 2" in logs
    assert "Output:" in logs
    assert "expr: division by zero" in logs


def test_walk_key_path():
    config = {"a": {"b": {"c": "cherry"}}}
    expected = {"c": "cherry"}
    assert utils.walk_key_path(config, ["a", "b"]) == expected


def test_walk_key_path_bad_key_path():
    config = {"a": {"b": {"c": "cherry"}}}
    with pytest.raises(KeyError):
        utils.walk_key_path(config, ["a", "x"])


def test_walk_key_path_bad_leaf_value():
    config = {"a": {"b": {"c": "cherry"}}}
    with pytest.raises(SystemExit):
        utils.walk_key_path(config, ["a", "b", "c"])
