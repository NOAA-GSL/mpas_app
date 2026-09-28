import pytest

from scripts import utils


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
