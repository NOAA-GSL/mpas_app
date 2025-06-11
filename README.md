# mpas_app

App for building and running the [MPAS-Model](https://github.com/NOAA-GSL/MPAS-Model).

## Issues

For bugs, questions, and requests related to the app, please use GitHub Issues in the `NOAA-GSL`/`mpas_app` repository. These will be monitored closely, and we will get back to you as quickly as possible.

## CONUS 3km Quickstart Guide - Jet or Hera

More detailed information on how the app runs and making changes to the model inputs can be found [further down](#getting-started).

1. Clone the app's `main` branch and navigate to its directory:

``` bash
git clone https://github.com/NOAA-GSL/mpas_app.git --recursive
cd mpas_app
```

2. Build the Model and components: `./build.sh -p <platform>`

3. Create your user yaml in the `ush` directory: the file itself can be as simple as:

``` yaml
user:
  experiment_dir: /path/to/exp/dir
  platform: jet
platform:
  account: wrfruc
```

4. Load the `mpas_app` conda environment. From the `mpas_app/` directory:

``` bash
source load_wflow_modules.sh <platform>
```

5. Generate the experiment:

``` bash
cd ush
./experiment_gen.py workflows/3km_conus.yaml workflows/conus.<platform>.yaml <your_user_yaml.yaml>
```

This generates an experiment directory at the path specified in your user YAML that contains a Rocoto XML file, which is ready to use.

## Getting Started

The `mpas_app` default is currently set to run on a 3-km CONUS mesh using GFS initial conditions and lateral boundary conditions. To get started, clone the app and navigate to its directory:

``` bash
git clone https://github.com/NOAA-GSL/mpas_app.git --recursive
cd mpas_app
```

When switching branches in the `mpas_app`, or if you forget to use the `--recursive` flag when cloning, you can run the following command from the `mpas_app` directory:

``` bash
git submodule update --init --recursive
```

## Building the Model

Currently, Jet and Hera are the only platforms fully supported on the `main` branch. To run the default build script:

``` bash
./build.sh -p <platform>
```

The app is partially supported on Ursa. UPP is not currently supported on that platform.

To see the different build options (including MPAS build options):

``` bash
./build.sh -h
```

This builds the MPAS-Model (based on MPAS release version `8.2.2`) and installs Miniconda inside the local clone. The `ungrib` conda environment installed in the process includes a pre-built package to run WPS Ungrib tool. The MPAS App build can take up to an hour to complete.

### default_config.yaml

`default_config.yaml` is the default YAML config file located in the `ush` directory of `mpas_app`. It is structured so that the top-level blocks are named based on the action they take in the MPAS App workflow, while the sub-sections often follow [`UW Tools YAML`](https://uwtools.readthedocs.io/en/main/sections/user_guide/yaml/components/index.html) for specific drivers.

The `user:` section is the most likely to need changing. Here there are a handful of common high-level configuration options that include cycle dates and cycling frequency, controls for boundary conditions, the mesh for the forecast grid, and the workflow blocks for which tasks to run.

The configuration settings under `get_ics_data` and `get_lbcs_data` define resources and configuration that retrieve the data needed for initial conditions and lateral boundary conditions from AWS by default.

The configuration settings under `prepare_grib_ics` and `prepare_grib_lbcs` define how the grib files will be processed with ungrib. The `ungrib:` blocks follow the [`UW YAML`](https://uwtools.readthedocs.io/en/main/sections/user_guide/yaml/components/ungrib.html) for the ungrib driver.

The `create_ics` and `create_lbcs` blocks define the [`mpas_init driver UW YAML`](https://uwtools.readthedocs.io/en/main/sections/user_guide/yaml/components/mpas_init.html). These sections are where namelist and streams XML settings for the `init_atmosphere_model` may be updated. The defaults also define all the necessary files to be linked or copied into the run directories, such as runtime tables from the MPAS `physics_wrf/files` directory and `stream_list` files.

The `forecast` section defines the MPAS `atmosphere_model` executable configuration. It follows the [`mpas driver UW YAML documentation`](https://uwtools.readthedocs.io/en/main/sections/user_guide/yaml/components/mpas_init.html). If you want to add additional physics, you should add them in the physics field of the atmosphere namelist user config (see below).

The `post` section configures three tasks in the workflow: a helper task that combines grib files (the command is coded directly into the Rocoto task), the MPASSIT run script (not a UW Driver), and the [`upp UW Driver`](https://uwtools.readthedocs.io/en/main/sections/user_guide/yaml/components/upp.html).

Any of the default settings can be overridden by providing a user YAML (see next section) that matches the same structure as the default settings.

### User Config YAML

A user-provided config (e.g. `<your_name>.yaml`) can be provided during the configuration step to update the default configuration with different settings. Rather than editing the default YAML or modifying files in run directories, track all changes in a single place that will define the full experiment for reproducible results. The file itself can be as simple as:

``` yaml
user:
  experiment_dir: /path/to/exp/dir
  platform: jet
platform:
  account: wrfruc
```

To update additional fields, you add the nested structure from `default_config.yaml` with the desired values. For example, to modify the physics for the `atmosphere` executable to include Thompson microphysics, add the following to the user config YAML:

``` yaml
forecast:
  mpas:
    namelist:
      update_values:
        physics:
          config_microp_scheme = 'mp_thompson'
```

For a deeper understanding of our configuration files, you can visit the [`uwtools`](https://uwtools.readthedocs.io/en/main/sections/user_guide/yaml/index.html) documentation on UW YAML.

To remove tasks from the workflow section, use the `uwtools` `!remove` tag on the entry to be removed. The same approach works on any setting in the default configs.

``` yaml
workflow:
  tasks:
    task_get_lbcs_data: !remove
    task_mpas_lbcs: !remove
```

This block in the user YAML will remove the lateral boundary tasks from the workflow.

## Generate the Experiment

Prior to generating and running the experiment, the appropriate environment will need to be activated. From the `mpas_app/` directory., run:

``` bash
source load_wflow_modules.sh <platform>
```

With user YAML named, `user_config.yaml`, create a fully configured experiment by running the following from the ``mpas_app/ush/` directory:

```
cd ush
./experiment_gen.py workflows/3km_conus.yaml workflows/conus.<platform>.yaml [optional.yaml] user_config.yaml
```

Any number of config YAMLs are accepted on the command line where the later the configuration setting is in the list, the higher priority it will have. In other words, the same setting altered in `optional.yaml` will be overwritten by the value in `user_config.yaml`.

This will create an experiment directory with an `experiment.yaml` file, which contains the user modifications to `default_config.yaml`. The experiment directory also contains a Rocoto XML file, which is ready to use with the command `rocotorun -w rocoto.xml -d rocoto.db`. You will have to iteratively run this command until all steps have been completed. You can check the status of these steps by running `rocotostat -w rocoto.xml -d rocoto.db`.

Logs are generated for each of the different tasks in the workflow, and `workflow.log` contains the submission and completion statuses in text format.

## Post-Processing

`MPASSIT` and `UPP` are used for post-processing and are included as submodules in the application, just like the `MPAS-Model`. Settings for post-processing components can be adjusted in your user configuration YAML, following the same nested structure described above.
