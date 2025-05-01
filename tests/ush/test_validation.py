import json
from copy import deepcopy
from datetime import datetime, timezone
from types import SimpleNamespace as ns
from typing import Any

from pydantic import ValidationError
from pytest import ExceptionInfo, fixture, mark, raises

from ush import validation

MSG = ns(
    dt="a valid datetime",
    ge0="greater than or equal to 0",
    gt0="greater than 0",
    int="a valid integer",
    list="a valid list",
    model="'GFS' or 'RAP'",
    str="a valid string",
)

# Tests


def test_validate__first_and_last_cycle(config):
    keys = ["last_cycle"]
    # Fine: last_cycle coincides with first_cycle
    last_cycle_fine = config["user"]["first_cycle"]
    validation.validate(with_set(config, last_cycle_fine, "user", *keys)["user"])
    # Wrong: last_cycle precedes first_cycle
    last_cycle_wrong = datetime(1970, 1, 1, 0, tzinfo=timezone.utc)
    with raises(ValidationError) as e:
        validation.validate(with_set(config, last_cycle_wrong, "user", *keys)["user"])
    assert "last_cycle cannot precede first_cycle" in str(e)


@mark.parametrize(
    ("keys", "msg", "val"),
    [
        (["cycle_frequency"], MSG.gt0, 0),
        (["cycle_frequency"], MSG.int, None),
        (["experiment_dir"], MSG.str, None),
        (["first_cycle"], MSG.dt, None),
        (["ics", "external_model"], MSG.model, "FOO"),
        (["ics", "offset_hours"], MSG.ge0, -1),
        (["ics", "offset_hours"], MSG.int, None),
        (["last_cycle"], MSG.dt, None),
        (["lbcs", "external_model"], MSG.model, "FOO"),
        (["lbcs", "interval_hours"], MSG.gt0, 0),
        (["lbcs", "interval_hours"], MSG.int, None),
        (["lbcs", "offset_hours"], MSG.ge0, -1),
        (["lbcs", "offset_hours"], MSG.int, None),
        (["mesh_label"], MSG.str, None),
        (["mpas_app"], MSG.str, None),
        (["platform"], MSG.str, None),
        (["workflow_blocks"], MSG.list, None),
        (["workflow_blocks"], MSG.str, [None]),
    ],
)
def test_validate__fail_values_bad(config, keys, msg, val):
    with raises(ValidationError) as e:
        validation.validate(with_set(config, val, "user", *keys)["user"])
    check(e, keys, f"Input should be {msg}")


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
def test_validate__fail_values_missing(config, keys):
    with raises(ValidationError) as e:
        validation.validate(with_del(config, "user", *keys)["user"])
    check(e, keys, "Field required")


def test_validate__pass(config):
    validation.validate(config["user"])


# Support


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


def check(e: ExceptionInfo[ValidationError], keys: list[str], msg: str):
    assert e.value.error_count() == 1
    info = json.loads(e.value.json())[0]
    assert info["loc"][: len(keys)] == keys
    assert info["msg"] == msg


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
