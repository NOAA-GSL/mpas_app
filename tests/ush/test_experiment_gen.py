import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from subprocess import CalledProcessError
from unittest.mock import Mock, patch

from pytest import fixture, raises
from uwtools.api.config import YAMLConfig, get_yaml_config
from uwtools.exceptions import UWConfigError

from ush import experiment_gen, validation


@fixture
def test_config(tmp_path):
    return {
        "user": {
            "first_cycle": "2023-09-15T00:00:00",
            "platform": "jet",
            "ics": {"external_model": "GFS"},
            "lbcs": {"external_model": "GFS"},
        },
        "data": {"mesh_files": str(tmp_path / "meshes")},
        "create_ics": {"mpas_init": {"execution": {"batchargs": {"cores": 32}}}},
        "forecast": {"mpas": {"execution": {"batchargs": {"nodes": 2, "tasks_per_node": 32}}}},
    }


@fixture
def validated_config(tmp_path):
    return validation.Config(
        user=validation.User(
            mesh_label="testmesh",
            driver_validation_blocks=["some.mpas", "some.upp"],
            experiment_dir=tmp_path,
            workflow_blocks=["block1.yaml"],
            cycle_frequency=6,
            first_cycle=datetime(2025, 1, 1, tzinfo=timezone.utc),
            last_cycle=datetime(2025, 1, 2, tzinfo=timezone.utc),
            ics=validation.ICs(external_model="GFS", offset_hours=0),
            lbcs=validation.LBCs(external_model="GFS", interval_hours=6, offset_hours=0),
            platform="jet",
        )
    )


def test_create_grid_files(tmp_path):
    src_mesh = tmp_path / "mesh.graph.info"
    exp_dir = tmp_path / "experiment"
    exp_dir.mkdir()
    src_mesh.write_text("mock content")
    with (
        patch("ush.experiment_gen.copy") as copy,
        patch("ush.experiment_gen.check_output") as check_output,
    ):
        check_output.return_value = "GPMetis output here"
        experiment_gen.create_grid_files(exp_dir, src_mesh, 32)
        copy.assert_called_once_with(src=src_mesh, dst=exp_dir)
        expected_cmd = f"gpmetis -minconn -contig -niter=200 {exp_dir / src_mesh.name} 32"
        check_output.assert_called_once_with(
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


def test_generate_workflow_files(tmp_path, test_config, validated_config):
    experiment_file = tmp_path / "experiment.yaml"
    mpas_app = tmp_path / "mpas_app"
    with (
        patch.object(
            experiment_gen, "get_yaml_config", return_value=YAMLConfig(test_config)
        ) as get_yaml_config,
        patch.object(experiment_gen, "validate_driver_blocks"),
        patch.object(experiment_gen, "realize") as realize,
        patch.object(experiment_gen.rocoto, "realize", return_value=True) as rocoto_realize,
        patch("sys.exit") as sysexit,
    ):
        experiment_gen.generate_workflow_files(
            get_yaml_config({}), experiment_file, mpas_app, validated_config
        )
        get_yaml_config.assert_called()
        realize.assert_called_once()
        rocoto_realize.assert_called_once()
        sysexit.assert_not_called()


def test_generate_workflow_files_failure(tmp_path, test_config, validated_config):
    experiment_file = tmp_path / "experiment.yaml"
    mpas_app = tmp_path / "mpas_app"
    with (
        patch.object(experiment_gen, "get_yaml_config", return_value=YAMLConfig(test_config)),
        patch.object(experiment_gen, "validate_driver_blocks"),
        patch.object(experiment_gen, "realize"),
        patch.object(experiment_gen.rocoto, "realize", return_value=False),
        patch("sys.exit") as sysexit,
    ):
        experiment_gen.generate_workflow_files(
            get_yaml_config({}), experiment_file, mpas_app, validated_config
        )
        sysexit.assert_called_once_with(1)


def test_main(validated_config, test_config, tmp_path):
    experiment_config = YAMLConfig(test_config)
    with (
        patch.object(experiment_gen, "parse_args", return_value=[tmp_path / "user.yaml"]),
        patch.object(
            experiment_gen,
            "prepare_configs",
            return_value=(experiment_config, Path("/some/mpas_app")),
        ),
        patch.object(experiment_gen, "validate", return_value=validated_config),
        patch.object(
            experiment_gen,
            "setup_experiment_directory",
            return_value=(tmp_path, tmp_path / "experiment.yaml"),
        ),
        patch.object(experiment_gen, "generate_workflow_files") as generate,
        patch.object(experiment_gen, "stage_grid_files") as stage,
    ):
        experiment_gen.main()
        generate.assert_called_once()
        stage.assert_called_once()


def test_parse_args():
    with patch("sys.argv", ["progname", "config1.yaml", "config2.yaml"]):
        result = experiment_gen.parse_args()
    assert result == [Path("config1.yaml"), Path("config2.yaml")]


def test_prepare_configs(test_config):
    config_dicts = [
        test_config,
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
        patch.object(experiment_gen, "get_yaml_config") as get_yaml_config,
        patch.object(experiment_gen, "Path") as path,
    ):
        get_yaml_config.side_effect = [YAMLConfig(cfg) for cfg in config_dicts]
        path.return_value.parent.parent.resolve.return_value = Path("/some/mpas_app")
        experiment_config, mpas_app = experiment_gen.prepare_configs([Path("user.yaml")])
    assert isinstance(experiment_config, YAMLConfig)
    assert experiment_config["data"]["mesh_files"] == test_config["data"]["mesh_files"]
    assert experiment_config["ics_key"] == "ics_value"
    assert experiment_config["lbcs_key"] == "lbcs_value"
    assert experiment_config["platform"] is True
    assert experiment_config["user"] is True
    assert mpas_app == Path("/some/mpas_app")


def test_required_nprocs(test_config):
    nprocs = experiment_gen.required_nprocs(test_config)
    assert nprocs == [32, 64]


def test_setup_experiment_directory(validated_config):
    validated_config.user.experiment_dir = validated_config.user.experiment_dir / "experiment"
    experiment_dir, experiment_file = experiment_gen.setup_experiment_directory(validated_config)
    assert experiment_dir.is_dir()
    assert experiment_file == experiment_dir / "experiment.yaml"


def test_stage_grid_files(test_config, validated_config):
    mesh_dir = Path(test_config["data"]["mesh_files"])
    mesh_dir.mkdir(parents=True, exist_ok=True)
    mesh_file = mesh_dir / "testmesh.graph.info"
    mesh_file.write_text("mock content")
    existing_part = validated_config.user.experiment_dir / f"{mesh_file.name}.part.32"
    existing_part.write_text("partitioned content")
    with patch.object(experiment_gen, "create_grid_files") as create:
        experiment_gen.stage_grid_files(
            test_config, validated_config.user.experiment_dir, validated_config
        )
    create.assert_called_once_with(validated_config.user.experiment_dir, mesh_file, 64)


def test_validate_driver_blocks(test_config):
    test_config["user"]["driver_validation_blocks"] = [
        "some.mpas",
        "some.ungrib",
    ]
    mpas, ungrib = Mock(), Mock()
    with patch.object(experiment_gen, "yaml_keys_to_classes") as mapping:
        mapping.return_value = {"mpas": mpas, "ungrib": ungrib}
        experiment_gen.validate_driver_blocks(test_config)
        mpas.assert_called_once()
        mpas().validate.assert_called_once()
        ungrib.assert_called_once()
        ungrib().validate.assert_called_once()


def test_validate_driver_blocks_failure(test_config):
    test_config["user"]["driver_validation_blocks"] = ["forecast.mpas"]
    with raises(UWConfigError):
        experiment_gen.validate_driver_blocks(YAMLConfig(test_config))


def test_validate_driver_blocks_leadtime(test_config):
    test_config["user"]["driver_validation_blocks"] = ["some.upp"]
    upp_config = Mock()
    upp = Mock(return_value=upp_config)
    with (
        patch.object(experiment_gen.inspect, "signature") as signature,
        patch.object(experiment_gen, "yaml_keys_to_classes") as mapping,
    ):
        signature.return_value.parameters = {"leadtime": timedelta(hours=0)}
        mapping.return_value = {"upp": upp}
        experiment_gen.validate_driver_blocks(test_config)
        upp.assert_called_once()
        upp_config.validate.assert_called_once()
        assert "leadtime" in upp.call_args.kwargs
