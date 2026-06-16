from datetime import timedelta
from unittest.mock import patch

from pytest import fixture, raises
from uwtools.api.config import get_yaml_config

from scripts import get_external_data


@fixture
def config():
    return get_yaml_config(
        {
            "ics": {
                "config": {
                    "config": "/path/to/data_locations.yaml",
                    "lead_times": ["6", "25", "6"],
                }
            }
        }
    )


def test_main(args, config):
    args.key_path = ["ics"]
    with (
        patch.object(get_external_data, "parse_args", return_value=args) as parse_args,
        patch.object(get_external_data, "retrieve_data", return_value=True) as retrieve,
        patch.object(get_external_data, "get_yaml_config", return_value=config),
    ):
        get_external_data.main()
        parse_args.assert_called_once()
        retrieve.assert_called_once_with(
            # config here is the return value from get_yaml_config. Code will return the config
            # object loaded from the data_locations.yaml.
            config=config,
            cycle=args.cycle,
            lead_times=[timedelta(hours=x) for x in range(6, 25, 6)],
            members=[-999],
        )


def test_main__files_not_staged(args, config):
    args.key_path = ["ics"]
    with (
        patch.object(get_external_data, "parse_args", return_value=args),
        patch.object(get_external_data, "retrieve_data", return_value=False),
        patch.object(get_external_data, "get_yaml_config", return_value=config),
        raises(SystemExit),
    ):
        get_external_data.main()
