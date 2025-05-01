from datetime import datetime, timezone

from pytest import fixture

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


def test_validate(config):
    validation.validate(config["user"])
