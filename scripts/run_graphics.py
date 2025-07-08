#!/usr/bin/env python3
"""
The runscript for pygraf.
"""
from pathlib import Path
from types import SimpleNamespace as ns

from scripts.common import parse_args
from scripts.utils import run_shell_cmd, walk_key_path


def run_pygraf(
    config_file: Path,
    cycle: datetime,
    key_path: list[str],
    ) -> None:

    expt_config = get_yaml_config(config_file)
    expt_config.realize(
            context={
                "cycle": cycle,
                }
            )
    cfg = ns(**walk_key_path(config=expt_config, key_path=key_path + ["config"]))
    specs_file = cfg.specs_file
    if specs_update := cfg.specs_update:
        specs = get_yaml_config(cfg.specs_file)
        specs.update_from(get_yaml_config(specs_update))
        specs_file = Path(cfg.graphics_output_path, "graphics_specs.yml")
        specs.dump(specs_file)

    args = (
       f"-d {cfg.input_data_location}",
       f"-f 0 {cfg.forecast_length} {cfg.output_interval}",
       f"--file_type prs",
       f"--file_tmpl {cfg.file_template}",
       f"--images {cfg.image_list} hourly",
       f"-m {cfg.identifier}",
       f"-n {cfg.ntasks}",
       f"-o {cfg.graphics_output_path}",
       f"-s {cycle.strfmt('%Y%m%d%H')}",
       f"--specs {cfg.specs_file}",
       f"--tiles {cfg.tiles}",
       f"-w {cfg.wait_between_output}",
       f"-z {cfg.zip_file_path}",
       )

    cmd = f"""
    conda activate pygraf
    python create_graphics.py maps {" ".join(args)}
    """
    run_shell_cmd(
        cmd=cmd,
        cwd=cfg.pygraf_path,
        log_output=True,
        task_name="pygraf",
        )

def main():
    args = parse_args()
    run_pygraf(
        config_file=args.config_file
        cycle=args.cycle,
        key_path=args.key_path,
        )

if __name__ == "__main__":
    main() # pragma: no cover
