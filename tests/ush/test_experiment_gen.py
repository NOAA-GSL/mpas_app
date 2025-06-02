import logging
from datetime import datetime, timezone
from pathlib import Path
from subprocess import CalledProcessError
from unittest.mock import MagicMock, patch

from pytest import fixture, raises
from uwtools.api.config import YAMLConfig, get_yaml_config

from ush import experiment_gen, validation


@fixture
def mock_config(tmp_path):
    return {
        "data": {"mesh_files": str(tmp_path / "meshes")},
        "create_ics": {"mpas_init": {"execution": {"batchargs": {"cores": 32}}}},
        "forecast": {"mpas": {"execution": {"batchargs": {"nodes": 2, "tasks_per_node": 32}}}},
        "user": {
            "platform": "jet",
            "ics": {"external_model": "GFS"},
            "lbcs": {"external_model": "GFS"},
        },
    }


def test_create_grid_files(tmp_path):
    src_mesh = tmp_path / "mesh.graph.info"
    exp_dir = tmp_path / "experiment"
    exp_dir.mkdir()
    src_mesh.write_text("mock content")
    with (
        patch("ush.experiment_gen.copy") as mock_copy,
        patch("ush.experiment_gen.check_output") as mock_check_output,
    ):
        mock_check_output.return_value = "GPMetis output here"
        experiment_gen.create_grid_files(exp_dir, src_mesh, 32)
        mock_copy.assert_called_once_with(src=src_mesh, dst=exp_dir)
        expected_cmd = f"gpmetis -minconn -contig -niter=200 {exp_dir / src_mesh.name} 32"
        mock_check_output.assert_called_once_with(
            expected_cmd, encoding="utf=8", shell=True, stderr=-2, text=True
        )


def test_create_grid_files_failure(tmp_path, caplog):
    src_mesh = tmp_path / "mesh.graph.info"
    exp_dir = tmp_path / "experiment"
    exp_dir.mkdir()
    src_mesh.write_text("mock content")
    error_output = "gpmetis error: segmentation fault"
    exception = CalledProcessError(returncode=1, cmd="gpmetis ...", output=error_output)
    with (
        patch("ush.experiment_gen.copy"),
        patch("ush.experiment_gen.check_output", side_effect=exception),
    ):
        caplog.set_level(logging.ERROR)
        with raises(SystemExit) as excinfo:
            experiment_gen.create_grid_files(exp_dir, src_mesh, 16)
        assert excinfo.value.code == 1
        assert "Error running command:" in caplog.text
        assert "gpmetis error: segmentation fault" in caplog.text
        assert "Failed with status: 1" in caplog.text


def test_generate_workflow_files(tmp_path):
    experiment_file = tmp_path / "experiment.yaml"
    mpas_app = tmp_path / "mpas_app"
    validated = MagicMock()
    validated.user.workflow_blocks = ["block1.yaml"]
    with (
        patch("ush.experiment_gen.get_yaml_config", return_value=MagicMock()) as get_yaml_config,
        patch("ush.experiment_gen.realize") as realize,
        patch("ush.experiment_gen.rocoto.realize", return_value=True) as rocoto_realize,
        patch("sys.exit") as mock_exit,
    ):
        from ush import experiment_gen

        experiment_gen.generate_workflow_files(
            get_yaml_config({}), experiment_file, mpas_app, validated
        )
        get_yaml_config.assert_called()
        realize.assert_called_once()
        rocoto_realize.assert_called_once()
        mock_exit.assert_not_called()


def test_generate_workflow_files_failure(tmp_path):
    experiment_file = tmp_path / "experiment.yaml"
    mpas_app = tmp_path / "mpas_app"
    validated = MagicMock()
    validated.user.workflow_blocks = ["block1.yaml"]
    with (
        patch("ush.experiment_gen.get_yaml_config", return_value=MagicMock()),
        patch("ush.experiment_gen.realize"),
        patch("ush.experiment_gen.rocoto.realize", return_value=False),
        patch("sys.exit") as mock_exit,
    ):
        from ush import experiment_gen

        experiment_gen.generate_workflow_files(
            get_yaml_config({}), experiment_file, mpas_app, validated
        )
        mock_exit.assert_called_once_with(1)


def test_main(mock_config, tmp_path):
    mocked_experiment_config = MagicMock()
    mocked_experiment_config.as_dict.return_value = mock_config
    mock_validated = MagicMock()
    mock_validated.user.mesh_label = "testmesh"
    mock_validated.user.experiment_dir = tmp_path
    mock_validated.user.workflow_blocks = []
    with (
        patch("ush.experiment_gen.parse_args", return_value=[tmp_path / "user.yaml"]),
        patch(
            "ush.experiment_gen.prepare_configs",
            return_value=(mocked_experiment_config, Path("/mock/mpas_app")),
        ),
        patch("ush.experiment_gen.validate", return_value=mock_validated),
        patch(
            "ush.experiment_gen.setup_experiment_directory",
            return_value=(tmp_path, tmp_path / "experiment.yaml"),
        ),
        patch("ush.experiment_gen.generate_workflow_files") as mock_generate,
        patch("ush.experiment_gen.stage_grid_files") as mock_stage,
    ):
        experiment_gen.main()
        mock_generate.assert_called_once()
        mock_stage.assert_called_once()


def test_parse_args():
    with patch("sys.argv", ["progname", "config1.yaml", "config2.yaml"]):
        result = experiment_gen.parse_args()
    assert result == [Path("config1.yaml"), Path("config2.yaml")]


def test_prepare_configs(mock_config):
    config_dicts = [
        mock_config,
        {"user": True},
        {"supp_config": True},
        {"platform": True},
        {
            "GFS": {
                "ics": {"ics_key": "ics_value"},
                "lbcs": {"lbcs_key": "lbcs_value"},
            }
        },
    ]
    with (
        patch("ush.experiment_gen.get_yaml_config") as mock_get_yaml_config,
        patch("ush.experiment_gen.Path") as mock_path,
    ):
        mock_get_yaml_config.side_effect = [YAMLConfig(cfg) for cfg in config_dicts]
        mock_path.return_value.parent.parent.resolve.return_value = Path("/mocked/mpas_app")
        experiment_config, mpas_app = experiment_gen.prepare_configs([Path("user.yaml")])
    assert isinstance(experiment_config, YAMLConfig)
    assert experiment_config["data"]["mesh_files"] == mock_config["data"]["mesh_files"]
    assert experiment_config["ics_key"] == "ics_value"
    assert experiment_config["lbcs_key"] == "lbcs_value"
    assert experiment_config["platform"] is True
    assert experiment_config["user"] is True
    assert mpas_app == Path("/mocked/mpas_app")


def test_required_nprocs(mock_config):
    nprocs = experiment_gen.required_nprocs(mock_config)
    assert nprocs == [32, 64]


def test_setup_experiment_directory(tmp_path):
    validated = validation.Config(
        user=validation.User(
            cycle_frequency=6,
            experiment_dir=tmp_path / "experiment",
            first_cycle=datetime(2025, 1, 1, tzinfo=timezone.utc),
            last_cycle=datetime(2025, 1, 2, tzinfo=timezone.utc),
            ics=validation.ICs(external_model="GFS", offset_hours=0),
            lbcs=validation.LBCs(external_model="GFS", interval_hours=6, offset_hours=0),
            mesh_label="mesh",
            platform="platform",
            workflow_blocks=[],
        )
    )
    experiment_dir, experiment_file = experiment_gen.setup_experiment_directory(validated)

    assert experiment_dir.exists()
    assert experiment_dir.is_dir()
    assert experiment_file == experiment_dir / "experiment.yaml"


def test_stage_grid_files(mock_config, tmp_path):
    validated = MagicMock()
    validated.user.mesh_label = "testmesh"
    validated.user.experiment_dir = tmp_path
    mesh_dir = Path(mock_config["data"]["mesh_files"])
    mesh_dir.mkdir(parents=True, exist_ok=True)
    mesh_file = mesh_dir / "testmesh.graph.info"
    mesh_file.write_text("mock content")
    existing_part = tmp_path / f"{mesh_file.name}.part.32"
    existing_part.write_text("partitioned content")
    with patch.object(experiment_gen, "create_grid_files") as mock_create:
        experiment_gen.stage_grid_files(mock_config, tmp_path, validated)
    mock_create.assert_called_once_with(tmp_path, mesh_file, 64)
