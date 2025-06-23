import sys
from pathlib import Path
from textwrap import dedent

from pytest import fixture

from scripts.utils import run_shell_cmd

root = Path(__file__).parent.parent


@fixture
def user_yaml(tmp_path):
    yaml = f"""
    user:
      experiment_dir: {tmp_path}
      platform: jet
    platform:
      account: wrfruc
    """
    path = tmp_path / "user.yaml"
    path.write_text(dedent(yaml).strip())
    return path


# TODO Use user-controlled temp space


def test_regtest_experiment_gen(user_yaml):
    experiment_dir = user_yaml.parent
    cmd = f"./experiment_gen.py workflows/3km_conus.yaml workflows/conus.jet.yaml {user_yaml}"
    success, output = run_shell_cmd(cmd, cwd=root / "ush")
    assert success
    for fn in [
        "experiment.yaml",
        "hrrrv5.graph.info",
        "hrrrv5.graph.info.part.768",
        "hrrrv5.graph.info.part.800",
        "rocoto.xml",
    ]:
        assert (experiment_dir / fn).is_file()
