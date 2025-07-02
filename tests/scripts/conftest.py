from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock

from pytest import fixture


@fixture
def args():
    args = Mock()
    args.config_file = Path("/some/config.yaml")
    args.cycle = datetime(2025, 1, 1, 12, tzinfo=timezone.utc)
    args.key_path = ["forecast"]
    return args
