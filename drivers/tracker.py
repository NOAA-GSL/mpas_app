"""
A driver for GFDL's Cyclone Tracker
"""
import json
import re
from datetime import timedelta
from itertools import chain
from pathlib import Path

from iotaa import asset, task, tasks

from uwtools.config.formats.yaml import YAMLConfig
from uwtools.config.formats.nml import NMLConfig
from uwtools.drivers.driver import DriverCycleBased
from uwtools.strings import STR
from uwtools.utils.file import writable
from uwtools.utils.processing import execute
from uwtools.utils.tasks import file, symlink



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
        yield [self.combined_input_files(), self.input_index_files()]
        content_list = [f"{i+1:4d} {fhr*60:5d}" for i, fhr in enumerate(self._input_file_map())]
        with writable(path) as f:
            f.write("\n".join(content_list))

    @property
    def _combined_file_tmpl(self):
        """
        The templated name of the combined grib file.
        """
        return "COMBINED.GrbF{fhr:02d}"

    @task
    def combined_input_files(self):
        """
        Concatinate the surface and PRSLEV files so the tracker has all the
        fields it needs.
        """
        yield self.taskname("input files")
        upp_files = self._input_file_map()
        combined_files = [self._combined_file_tmpl.format(fhr=fhr) for fhr in upp_files]
        yield [file(self.rundir/p) for p in combined_files]
        all_input_files = list(chain.from_iterable(upp_files.values()))
        yield [file(Path(p)) for p in all_input_files]
        self.rundir.mkdir(exist_ok=True)
        for fhr, infiles in upp_files.items():
            combined_file = self._combined_file_tmpl.format(fhr=fhr)
            execute(
                cmd=f"cat {' '.join(infiles)} > {combined_file}",
                cwd=self.rundir,
                log_output=True,
                )

    @tasks
    def input_files(self):
        """
        The UPP-processed, combined forecast files.
        """
        yield self.taskname("input files")
        upp_files = self._input_file_map()
        symlinks = {}
        for fhr in upp_files:
            linkname = f"mpas.trak.all.{self.cycle.strftime('%Y%m%d%H')}.f{fhr * 60:05d}"
            target = self.rundir / self._combined_file_tmpl.format(fhr=fhr)
            symlinks[target] = linkname
        yield [symlink(target=t, linkname=self.rundir / l) for t, l in symlinks.items()]


    @task
    def input_index_files(self):
        """
        The Grib2 index files
        """
        yield self.taskname("input index files")
        index_files = {}
        for fhr in self._input_file_map():
            infile = str(self.rundir /
                    f"mpas.trak.all.{self.cycle.strftime('%Y%m%d%H')}.f{fhr * 60:05d}")
            indexfile = f"{infile}.ix"
            index_files[infile] = str(self.rundir / indexfile)
        yield [file(Path(idx)) for idx in index_files.values()]
        yield self.input_files()
        self.rundir.mkdir(exist_ok=True)
        envcmds = self.config["execution"]["envcmds"]
        for infile, idx in index_files.items():
            execute(
                cmd=f"{' && '.join(envcmds)} && grb2index {infile} {idx}",
                cwd=self.rundir,
                log_output=True,
                )

    @task
    def input_vitals(self):
        """
        Theh TC vitals input data
        """
        fn = "allvit"
        yield self.taskname("TC vitals input file {fn}")
        path = self.rundir / fn
        yield asset(path, path.is_file)
        tcvitals = Path(self.config["tcvitals"])
        yield file(tcvitals)
        datestr = self.cycle.strftime("%Y%m%d %H")
        data = {}
        with open(tcvitals, "r", encoding="utf-8") as f:
            for line in f:
                if datestr in line:
                    match = re.match(r'^(.{19})(.*)$', line)
                    if match:
                        key = match.group(1)
                        value = f"{match.group(1)}{match.group(2)}"
                        data[key] = value
        content = [data[k] for k in sorted(data)]
        with writable(path) as f:
            f.write("\n".join(content))

    @task
    def input_vitals_other_names(self):
        """
        TC Vitals file named differently.
        """
        fns = ["tcvit_rsmc_storms.txt", "fort.12"]
        yield self.taskname("TC vitals input file {' & '.join(fns)}")
        paths = [self.rundir / fn for fn in fns]
        yield [asset(path, path.is_file) for path in paths]
        yield self.input_vitals()
        for path in paths:
            symlink(target=self.rundir/ "allvit", linkname=path)

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
        self._create_user_updated_config(
            config_class=NMLConfig,
            config_values=namelist,
            path=path,
        )

    @tasks
    def provisioned_rundir(self):
        """
        Run directory provisioned with all required content.
        """
        yield self.taskname(f"provisioned run directory: {str(self.rundir)}")
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


    @task
    def runscript(self):
        """
        The runscript.
        """
        path = self._runscript_path
        yield self.taskname(path.name)
        yield asset(path, path.is_file)
        yield None
        self._write_runscript(path=path)

    # Private helper methods

    @property
    def driver_name(self) -> str:
        """
        Returns the name of this driver.
        """
        return "gfdl-tracker"

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
            filemap[fhr] = configobj["filepaths"]
        return filemap
