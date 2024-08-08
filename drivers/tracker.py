"""
A driver for GFDL's Cyclone Tracker
"""
import os

from iotaa import asset, task, tasks

from uwtools.config.jinja2 import render
from uwtools.drivers.driver import DriverCycleBased
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
        yield self._taskname("input fcst minutes file")
        path = self._rundir / fn
        yield asset(path, path.is_file)
        yield [self.input_files(), self.input_index_files()]
        content_list = [f"{i+1:4d} {fhr*60:5d}" for i, fhr in enumerate(self._input_file_map)]
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(content_list))


    @tasks
    def input_files(self):
        """
        The UPP-processed forecast files.
        """
        yield self._taskname("input files")
        upp_files = self._input_file_map()
        symlinks = {}
        for fhr, upp_file in upp_files.items():
            linkname = f"mpas.track.all.{self.cycle.strftime('%Y%m%d%H')}.f{fhr * 60:05d}"
            symlinks[upp_file] = linkname
        yield [symlink(target=t, linkname=l) for t, l in symlinks.items()]]


    @tasks
    def input_index_files(self):
        """
        The Grib2 index files
        """
        yield self._taskname("input index files")
        upp_files = self._input_file_map()
        index_files = {}
        for fhr in self._input_file_map():
            infile = f"mpas.track.all.{self.cycle.strftime('%Y%m%d%H')}.f{fhr * 60:05d}"
            indexfile = f"{infile}.ix"
            index_files[infile] = indexfile
        yield [file(idx) for idx in index_files.values()]
        for infile, idx in index_files.items(): 
            execute(
                cmd=f"grb2index {infile} {idx}"
                cwd=self.rundir,
                env=os.environ,
                log_output=True,
                )


    @task
    def input_vitals(self):
        """
        Theh TC vitals input data
        """
        fn = "allvit"
        yield self._taskname("TC vitals input file {fn}")
        path = self._rundir / fn
        yield asset(path, path.is_file)
        tcvitals = Path(self.config["tcvitals"])
        yield file(tcvitals)
        datestr = self.cycle.strftime("%Y%m%d %H")
        data = []
        with open(tcvitals, "r", encoding="utf-8") as f:
            line = f.readline().strip()
            if datestr in line:
                match = re.match(r'^(.{19})(.*)$', line)
                if match:
                    key = match.group(1)
                    value = f"{match.group(1)}{match.group(2)}"
                    data[key] = value
        content = [data[k] for k in sorted(data)]
        with open(fn, "w", encoding="utf-8") as f:
            f.write("\n".join(content))


    @task
    def namelist_file(self):
        """
        The namelist file
        """
        fn = "namelist.gettrk"
        yield self._taskname(f"namelist file {fn}")
        path = self._rundir / fn
        yield asset(path, path.is_file)
        input_files = []
        namelist = self._driver_config[STR.namelist]
        if base_file := namelist.get(STR.basefile):
            input_files.append(base_file)
        yield [file(Path(input_file)) for input_file in input_files]
        self._create_user_updated_config(
            config_class=NMLConfig,
            config_values=namelist,
            path=path,
            schema=self._namelist_schema(),
        )


    @tasks
    def provisioned_rundir(self):
        """
        Run directory provisioned with all required content.
        """
        yield self._taskname("provisioned run directory")
        yield [
            self.input_fcst_minutes(),
            self.input_files(),
            self.input_index_files(),
            self.input_vitals(),
            self.namelist_file(),
            self.runscript(),
        ]


    @task
    def runscript(self):
        """
        The runscript.
        """
        path = self._runscript_path
        yield self._taskname(path.name)
        yield asset(path, path.is_file)
        yield None
        self._write_runscript(path=path)

    # Private helper methods

    @property
    def _driver_name(self) -> str:
        """
        Returns the name of this driver.
        """
        return STR.tracker

    def _input_file_map(self) -> dict:
        """
        Return a map of forecast hour to UPP file name.
        """
        infiles = self._driver_config["input_files"]
        endhour = infiles["endhour"]
        filefreq = infiles["filefreq"]
        file_map = {}
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


set_driver_docstring(GFDLTracker)
