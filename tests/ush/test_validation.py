import json
from copy import deepcopy
from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Any

from pydantic import ValidationError
from pytest import ExceptionInfo, fixture, mark, raises

from ush import validation

MSG = SimpleNamespace(
    dt="a valid datetime",
    ge0="greater than or equal to 0",
    gt0="greater than 0",
    int="a valid integer",
    list="a valid list",
    model="'GFS' or 'RAP'",
    str="a valid string",
)

# Tests


def test_validate__user_driver_validation_blocks(config):
    keys = ["user", "driver_validation_blocks"]
    # Fine: one of the uwtools drivers
    valid_blocks = ["some.ungrib", "some.mpas_init", "some.mpas", "some.upp"]
    validation.validate(with_set(config, valid_blocks, *keys))
    # Fine: no driver_validation_blocks specified
    config_without_block = with_del(config, *keys)
    validation.validate(config_without_block)
    # Wrong: unsupported driver
    unsupported_drivers = ["some.typo", "some.wrong.driver"]
    with raises(ValidationError) as e:
        validation.validate(with_set(config, unsupported_drivers, *keys))
    assert "Unsupported driver in 'driver_validation_blocks'" in str(e.value)


def test_validate__user_first_and_last_cycle(config):
    keys = ["user", "last_cycle"]
    # Fine: last_cycle coincides with first_cycle.
    last_cycle_fine = config["user"]["first_cycle"]
    validation.validate(with_set(config, last_cycle_fine, *keys))
    # Wrong: last_cycle precedes first_cycle.
    last_cycle_wrong = datetime(1970, 1, 1, 0, tzinfo=timezone.utc)
    with raises(ValidationError) as e:
        validation.validate(with_set(config, last_cycle_wrong, *keys))
    assert "last_cycle cannot precede first_cycle" in str(e)


@mark.parametrize(
    ("keys", "msg", "val"),
    [
        (["cycle_frequency"], MSG.gt0, 0),
        (["cycle_frequency"], MSG.int, None),
        (["driver_validation_blocks"], MSG.str, [None]),
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
        (["platform"], MSG.str, None),
        (["workflow_blocks"], MSG.list, None),
        (["workflow_blocks"], MSG.str, [None]),
    ],
)
def test_validate__user_fail_values_bad(config, keys, msg, val):
    keys = ["user", *keys]
    with raises(ValidationError) as e:
        validation.validate(with_set(config, val, *keys))
    check(e, keys, f"Input should be {msg}")


def test_validate__user_fail_values_bad_experiment_dir(config):
    keys = ["user", "experiment_dir"]
    with raises(ValidationError) as e:
        validation.validate(with_set(config, None, *keys))
    check(e, keys, "Input is not a valid path")


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
        ["platform"],
        ["workflow_blocks"],
    ],
)
def test_validate__user_fail_values_missing(config, keys):
    keys = ["user", *keys]
    with raises(ValidationError) as e:
        validation.validate(with_del(config, *keys))
    check(e, keys, "Field required")


def test_validate__pass(config):
    validated = validation.validate(config)
    # Config object supports dotted attribute lookup:
    assert validated.user.cycle_frequency == 12
    # Config object can be dumped to a dict:
    d1 = validated.model_dump()
    assert isinstance(d1, dict)
    assert d1["user"]["ics"]["external_model"] == "GFS"
    assert isinstance(d1["user"]["first_cycle"], datetime)
    assert d1["user"]["first_cycle"] == config["user"]["first_cycle"]
    # Config object can be dumped to a JSON-compatible dict:
    d2 = validated.model_dump(mode="json")
    assert isinstance(d2, dict)
    assert d2["user"]["ics"]["external_model"] == "GFS"
    assert isinstance(d2["user"]["first_cycle"], str)
    assert d2["user"]["first_cycle"] == "2025-04-30T12:00:00Z"


# Support


@fixture
def config(tmp_path):
    return {
        "user": {
            "cycle_frequency": 12,
            "driver_validation_blocks": ["forecast.mpas", "post.upp"],
            "experiment_dir": tmp_path,
            "first_cycle": datetime(2025, 4, 30, 12, tzinfo=timezone.utc),
            "ics": {"external_model": "GFS", "offset_hours": 0},
            "last_cycle": datetime(2025, 4, 30, 18, tzinfo=timezone.utc),
            "lbcs": {"external_model": "GFS", "interval_hours": 6, "offset_hours": 0},
            "mesh_label": "hrrrv5",
            "platform": "big_computer",
            "workflow_blocks": ["cold_start.yaml", "post.yaml"],
        }
    }


def check(e: ExceptionInfo[ValidationError], keys: list[str], msg: str):
    assert e.value.error_count() == 1
    info = json.loads(e.value.json())[0]
    assert info["loc"][: len(keys)] == keys
    assert info["msg"].startswith(msg)


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
