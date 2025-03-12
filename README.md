# mpas_app
App for building and running the [MPAS-Model](https://github.com/NOAA-GSL/MPAS-Model).

## Issues

For bugs, questions, and requests related to the app, please use either GitHub Discussions or GitHub Issues in the `NOAA-GSL`/`mpas_app` repository.  These will be monitored closely, and we will get back to you as quickly as possible. 

## CONUS 3km Quickstart Guide (Jet only)

More detailed information on how the app runs and making changes to the model inputs can be found [further down](#getting-started).

1. Clone the app's `conus_jet` branch and navigate to its directory:
```
git clone https://github.com/NOAA-GSL/mpas_app.git -b conus_jet --recursive
cd mpas_app
```
2. Build the Model and components: `./build.sh -p=jet`
3. Create your user yaml in the `ush` directory: the file itself can be as simple as:
```
user:
  experiment_dir: /path/to/exp/dir
  platform: jet
platform:
  account: wrfruc
```
4. Load the `mpas_app` conda environment: `source load_wflow_modules.sh jet` from the `mpas_app/` directory
5. Generate the experiment: 
```
cd ush
python experiment_gen workflows/conus.jet.yaml <your_user_yaml.yaml>
```
This generates an experiment directory at the path specified in your user YAML that contains a Rocoto XML file, which is ready to use.

## Getting Started

Clone the app and navigate to its directory:

```
git clone https://github.com/NOAA-GSL/mpas_app.git --recursive
cd mpas_app
```

When switching branches in the `mpas_app`, or if you forget to use the `--recursive` flag when cloning, you can run the following command from the `mpas_app` directory:

```
git submodule update --init --recursive
```


## Building the Model

Currently, Jet is the only platform supported on the `conus_jet` branch.  To run the default build script:

`./build.sh -p=jet`

To see the different build options (including MPAS build options):

`./build.sh -h`

This builds the MPAS-Model (version `8.2.2`) and installs Miniconda inside the local clone.  The `ungrib` conda environment installed in the process includes a pre-built package to run WPS Ungrib tool.  The build can take up to an hour to complete.

### default_config.yaml

`default_config.yaml` is the default YAML config file located in the `ush` directory of `mpas_app`.  

The `grid_files` field references the decomposed domain files from the previous step.

The fields under `prepare_ungrib` will retrieve the data you need for RAP initial conditions and lateral boundary conditions from AWS by default and will ungrib them.

Next, the `create_ics` part of the workflow creates the MPAS initial conditions using 4 cores and copies and links the files needed from when the model was built.  It also updates the `init_atmosphere` namelist.  Additional files, such as the runtime tables from the MPAS `physics_wrf/files` directory will go in this section of your user config YAML. The input/output file names are modified in the `streams:` field and the keys correspond to the template in the `parm/` directory.

A similar process is followed to create the lateral boundary conditions in the `create_lbcs` part of the workflow, the namelist and streams fields can be modified in the user config YAML.

Finally, the `forecast` step runs the MPAS `atmosphere` executable.  If you want to add additional physics, you should add them in the physics field of the atmosphere namelist user config (see below).

### User Config YAML

Your user config (e.g. `<your_name>.yaml`) is how you update the default configuration with different settings.  Rather than going through and changing all of the different namelist and streams files that the MPAS Model produces, you only need to create and update the single user config file in the `ush` directory.  The file itself can be as simple as:
```
user:
  experiment_dir: /path/to/exp/dir
  platform: jet
platform:
  account: wrfruc
```
To update additional fields, you add the nested structure from `default_config.yaml` with the additional information.  For example, to modify the physics for the `atmosphere` executable to include Thompson microphysics, you would add the following to the user config YAML:
```
forecast:
  mpas:
    namelist:
      update_values:
        physics:
          config_microp_scheme = 'mp_thompson'
```
For a deeper understanding of our configuration files, you can visit the [`uwtools`](https://uwtools.readthedocs.io/en/main/sections/user_guide/yaml/index.html) documentation on UW YAML. 

To remove tasks from the workflow section, use the `uwtools` `!remove` tag on the entry to be removed. The same approach works on any setting in the default configs.

```
workflow:
  tasks:
    task_get_lbcs_data: !remove
    task_mpas_lbcs: !remove
```

This block in your user YAML will remove the lateral boundary tasks from the workflow.


## Generate the Experiment

Prior to generating and running the experiment, you must run the command `source load_wflow_modules.sh jet` from the `mpas_app/` directory. 

When you have a completed user config YAML, you can run the `experiment_gen.py` script from the `ush/` directory to generate the MPAS experiment for a CONUS run:

`python experiment_gen.py workflows/conus.jet.yaml [optional.yaml] <user_config.yaml>`

Any number of config YAMLs are accepted on the command line where the later the configuration setting is in the list, the higher priority it will have. In other words, the same setting altered in `optional.yaml` will be overwritten by the value in `user_config.yaml`.

This will create an experiment directory with an `experiment.yaml` file, which contains the user modifications to `default_config.yaml`.  The experiment directory also contains a Rocoto XML file, which is ready to use with the command `rocotorun -w rocoto.xml -d rocoto.db`. You will have to iteratively run this command until all steps have been completed. You can check the status of these steps by running `rocotostat -w rocoto.xml -d rocoto.db`. 

Logs are generated for each of the different tasks in the workflow, and `workflow.log` contains the submission and completion statuses in text format.

## Post-Processing 

`MPASSIT` and `UPP` are used for post-processing and are included as submodules in the application, just like the `MPAS-Model`. Settings for post-processing components can be adjusted in your user configuration YAML, following the same nested structure described above. 
