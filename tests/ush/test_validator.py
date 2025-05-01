import re
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

from pydantic import ValidationError
from pytest import fixture, mark, raises

from ush import validation


@fixture
def config():
    return {
        "user": {
            "cycle_frequency": 12,
            "experiment_dir": "/path/to/dir",
            "first_cycle": datetime(2025, 4, 30, 12, tzinfo=timezone.utc),
            "ics": {"external_model": "GFS", "offset_hours": 0},
            "last_cycle": datetime(2025, 4, 30, 18, tzinfo=timezone.utc),
            "lbcs": {"external_model": "GFS", "interval_hours": 6, "offset_hours": 0},
            "mesh_label": "hrrrv5",
            "mpas_app": "",
            "platform": "big_computer",
            "workflow_blocks": ["cold_start.yaml", "post.yaml"],
        }
    }


# Tests


@mark.parametrize(
    "keys",
    [
        ["cycle_frequency"],
        ["experiment_dir"],
        ["first_cycle"],
        ["ics", "external_model"],
        ["ics", "offset_hours"],
        ["last_cycle"],
        ["lbcs", "external_model"],
        ["lbcs", "interval_hours"],
        ["lbcs", "offset_hours"],
        ["mesh_label"],
        ["mpas_app"],
        ["platform"],
        ["workflow_blocks"],
    ],
)
def test_validate__required_items(config, keys):
    with raises(ValidationError) as e:
        validation.validate(with_del(config, "user", *keys)["user"])
    assert re.search(r"1 validation error.*%s" % ".".join(keys), str(e), re.DOTALL)


def test_validate__ok(config):
    validation.validate(config["user"])


# Support


def with_del(d: dict, *args: Any) -> dict:
    """
    Delete a value at a given chain of keys in a dict.

    :param d: The dict to update.
    :param args: One or more keys navigating to the value to delete.
    """
    new = deepcopy(d)
    p = new
    for key in args[:-1]:
        p = p[key]
    del p[args[-1]]
    return new


def with_set(d: dict, val: Any, *args: Any) -> dict:
    """
    Set a value at a given chain of keys in a dict.

    :param d: The dict to update.
    :param val: The value to set.
    :param args: One or more keys navigating to the value to set.
    """
    new = deepcopy(d)
    p = new
    for key in args[:-1]:
        p = p[key]
    p[args[-1]] = val
    return new
