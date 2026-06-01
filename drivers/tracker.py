"""
A driver for GFDL's Cyclone Tracker
"""

import re
from datetime import timedelta
from pathlib import Path

from iotaa import asset, task, tasks
from uwtools.config.formats.nml import NMLConfig
from uwtools.config.formats.yaml import YAMLConfig
from uwtools.config.validator import validate_internal
from uwtools.drivers.driver import Assets, DriverCycleBased
from uwtools.strings import STR
from uwtools.utils.file import writable
from uwtools.utils.processing import run_shell_cmd
from uwtools.utils.tasks import file, symlink

from ush.validation import TrackerNamelist


class GFDLTracker(DriverCycleBased):
    """
    A driver for the GFDL Tracker
    """

    # Workflow tasks

    @task
    def input_fcst_minutes(self):
        """
        The input.fcst_minutes (fort.15) file.
        """
        fn = "fort.15"
        yield self.taskname("input fcst minutes file")
        path = self.rundir / fn
        yield asset(path, path.is_file)
        yield [self.input_files(), self.input_index_files()]
        content_list = [f"{i + 1:4d} {fhr * 60:5d}" for i, fhr in enumerate(self._input_file_map())]
        with writable(path) as f:
            f.write("\n".join(content_list))

    @tasks
    def input_files(self):
        """
        The UPP-processed, combined forecast files.
        """
        yield self.taskname("input files")
        upp_files = self._input_file_map()
        symlinks = {}
        for fhr, target in upp_files.items():
            linkname = f"mpas.trak.all.{self.cycle.strftime('%Y%m%d%H')}.f{fhr * 60:05d}"
            symlinks[target] = linkname
        yield [
            symlink(target=Path(target), linkname=self.rundir / link)
            for target, link in symlinks.items()
        ]

    @task
    def input_index_files(self):
        """
        The Grib2 index files
        """
        yield self.taskname("input index files")
        index_files = {}
        for fhr in self._input_file_map():
            infile = str(
                self.rundir / f"mpas.trak.all.{self.cycle.strftime('%Y%m%d%H')}.f{fhr * 60:05d}"
            )
            indexfile = f"{infile}.ix"
            index_files[infile] = str(self.rundir / indexfile)
        yield [asset(Path(idx), Path(idx).is_file) for idx in index_files.values()]
        yield [self.input_files()]
        self.rundir.mkdir(exist_ok=True)
        envcmds = self.config["execution"]["envcmds"]
        for infile, idx in index_files.items():
            run_shell_cmd(
                cmd=f"{' && '.join(envcmds)} && grb2index {infile} {idx}",
                cwd=self.rundir,
                log_output=True,
            )

    @task
    def input_vitals(self):
        """
        The TC vitals input data
        """
        fn = "allvit"
        yield self.taskname(f"TC vitals input file {fn}")
        path = self.rundir / fn
        yield asset(path, path.is_file)
        tcvitals = Path(self.config["tcvitals"])
        yield file(tcvitals)
        datestr = self.cycle.strftime("%Y%m%d %H")
        basins = self.config["basins"]
        storms = []
        with tcvitals.open() as f:
            for line in f:
                if datestr in line:
                    # Get all the storms in the required basins
                    # Matches: NHC  13L MELISSA   20251021 1200 143N 0713W 280 062.....
                    pattern = r"^.{5}[0-49][0-9][%s].{11}%s.*$" % (basins, datestr)
                    match = re.match(pattern, line)
                    if match:
                        storms.append(match.group(0))
        with writable(path) as f:
            f.write("\n".join(storms))

    @task
    def input_vitals_other_names(self):
        """
        TC Vitals file named differently.
        """
        fns = ["tcvit_rsmc_storms.txt", "fort.12"]
        yield self.taskname(f"TC vitals input file {' & '.join(fns)}")
        paths = [self.rundir / fn for fn in fns]
        yield [asset(path, path.is_file) for path in paths]
        yield self.input_vitals()
        for path in paths:
            symlink(target=self.rundir / "allvit", linkname=path)

    @task
    def namelist_file(self):
        """
        The namelist file
        """
        fn = "namelist.gettrk"
        yield self.taskname(f"namelist file {fn}")
        path = self.rundir / fn
        yield asset(path, path.is_file)
        input_files = []
        namelist = self.config[STR.namelist]
        if base_file := namelist.get(STR.basefile):
            input_files.append(base_file)
        yield [file(Path(input_file)) for input_file in input_files]
        self.create_user_updated_config(
            config_class=NMLConfig,
            config_values=namelist,
            path=path,
        )

    @tasks
    def provisioned_rundir(self):
        """
        Run directory provisioned with all required content.
        """
        yield self.taskname(f"provisioned run directory: {self.rundir}")
        self.rundir.mkdir(exist_ok=True)
        yield [
            self.input_fcst_minutes(),
            self.input_files(),
            self.input_index_files(),
            self.input_vitals(),
            self.input_vitals_other_names(),
            self.namelist_file(),
            self.runscript(),
        ]

    # Private helper methods

    @classmethod
    def driver_name(cls) -> str:
        """
        Returns the name of this driver.
        """
        return "gfdltracker"

    def _input_file_map(self) -> dict:
        """
        Return a map of forecast hour to UPP file name.
        """
        infiles = self.config["input_files"]
        endhour = infiles["endhour"]
        filefreq = infiles["filefreq"]
        filemap = {}
        for fhr in range(0, endhour + 1, filefreq):
            leadtime = timedelta(hours=fhr)
            configobj = YAMLConfig(infiles)
            configobj.dereference(
                context={
                    "cycle": self.cycle,
                    "leadtime": leadtime,
                    **self.config_full,
                }
            )
            filemap[fhr] = configobj["filepath"]
        return filemap

    def _validate(self) -> None:
        """
        Perform all necessary schema and pydantic validation.

        :raises: UWConfigError if validation fails.
        """
        Assets._validate(self)  # noqa: SLF001
        validate_internal(
            schema_name=STR.platform,
            desc="platform config",
            config_data=self._config_intermediate,
        )
        TrackerNamelist(**self.config["namelist"]["update_values"])
