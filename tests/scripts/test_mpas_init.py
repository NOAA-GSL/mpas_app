from unittest.mock import call, patch

from pytest import mark
from uwtools.api.config import get_yaml_config
from uwtools.api.driver import Driver

from scripts import mpas_init


@mark.parametrize("model", ["RAP", "RRFS"])
def test_main(args, model, tmp_path):
    config = {"user": {"ics": {"external_model": model}}}
    yaml_config = get_yaml_config(config)
    yaml_file = tmp_path / "config.yaml"
    yaml_config.dump(yaml_file)
    args.config_file = yaml_file
    args.key_path = "create_ics"
    with (
        patch.object(mpas_init, "parse_args", return_value=args) as parse_args,
        patch.object(
            mpas_init,
            "run_component",
            return_value=Driver,
        ) as run_component,
        patch.object(mpas_init, "variables_from_fix") as variables_from_fix,
    ):
        mpas_init.main()
        parse_args.assert_called_once()
        run_component.assert_called_once_with(
            driver_class=mpas_init.MPASInit,
            config_file=args.config_file,
            cycle=args.cycle,
            key_path=args.key_path,
        )
        if model == "RAP":
            variables_from_fix.assert_not_called()
        else:
            variables_from_fix.assert_called_once()


def test_variables_from_fix():
    config = {
        "rundir": "/some/path",
        "files_to_link": {"shdmax.123.nc": "foo", "shdmin.123.nc": "foo"},
        "streams": {"output": {"filename_template": "/some/filename"}},
        "user": {"mesh_label": "123"},
    }
    test_config = get_yaml_config(config)
    cmd = "module load nco ; ncks -A -v {var} foo /some/filename"
    expected_calls = [
        call(
            cmd=cmd.format(var=var),
            cwd="/some/path",
            log_output=True,
            taskname="variables_from_fix",
        )
        for var in ("shdmax", "shdmin")
    ]
    with patch.object(mpas_init, "run_shell_cmd") as run_shell_cmd:
        mpas_init.variables_from_fix(test_config, test_config)
        run_shell_cmd.assert_has_calls(expected_calls)
