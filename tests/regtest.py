from pathlib import Path
from textwrap import dedent

from pytest import fixture

from scripts.utils import run_shell_cmd

ROOT = Path(__file__).parent.parent

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

# NB: Keep tests in the order they need to run, not necessarily alphabetical.

def test_regtest_executables_exist():
    for fn in [
        "atmosphere_model",
        "init_atmosphere_model",
        "mpassit",
        "upp.x",
    ]:
        assert (ROOT / "exec" / fn).is_file()


def test_regtest_execute_experiment_gen_3km_conus(file_regression, user_yaml):
    experiment_dir = user_yaml.parent
    cmd = f"./experiment_gen.py workflows/3km_conus.yaml workflows/conus.jet.yaml {user_yaml}"
    success, output = run_shell_cmd(cmd, cwd=ROOT / "ush")
    assert success
    for fn in [
        "experiment.yaml",
        "hrrrv5.graph.info",
        "hrrrv5.graph.info.part.768",
        "hrrrv5.graph.info.part.800",
        "rocoto.xml",
    ]:
        assert (experiment_dir / fn).is_file()
    for fn in ["experiment.yaml", "rocoto.xml"]:
        file_regression.check(contents=(experiment_dir / fn).read_text(), extension=f".{fn}")
