from scripts import common

from pathlib import Path
from datetime import datetime

def test_parse_common_args_valid():
    argv = [
        "-c", "config.yaml",
        "--cycle", "2024-01-01T00:00:00",
        "--lead", "6",
        "--key-path", "forecast.model",
    ]
    args = common.parse_common_args(argv)
    assert args.config_file == Path("config.yaml")
    assert args.cycle == datetime(2024, 1, 1, 0, 0)
    assert args.lead == 6
    assert args.key_path == ["forecast", "model"]