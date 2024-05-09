# mpas_app
App for building and running the [MPAS-Model](https://github.com/NOAA-GSL/MPAS-Model)

## Getting Started

Clone the app and navigate to its directory:

```
git clone https://github.com/NOAA-GSL/mpas_app.git --recursive
cd mpas_app
```

If you forget the ``--recursive`` flag when you clone, or if you switch branches on `mpas_app`, from the clone:

```
git submodule update --init --recursive
```


## Building the Model

Currently Hera and Jet are the only platforms supported.  To run the default build script:

`./build.sh -p=<platform>`

To see the different build options (including MPAS build options):

`./build.sh -h`

This builds the MPAS-Model and installs Miniconda inside the local clone.  The `ungrib` conda environment installed in the process includes a pre-built package to run WPS Ungrib tool.

### default_config.yaml

`default_config.yaml` is the default yaml config file located in the `ush` directory of `mpas_app`.  

The `grid_files` field references the decomposed domain files from the previous step.

The fields under `prepare_ungrib` will retrieve whatever data you need for GFS initial conditions and lateral boundary conditions from AWS by default, and will ungrib them.

Next, the `create_ics` part of the worfklow creates the MPAS initial conditions using 4 cores and copies and links the files needed from when the model was built.  It also updates the `init_atmosphere` namelist.  Additional files like the runtime tables from the MPAS `physics_wrf/files` directory will go in this section of your user config yaml. The input/output file names are modified in the `streams:` field and the keys correspond to the template in the `parm/` directory.

A similar process is followed to create the lateral boundary conditions in the `create_lbcs` part of the workflow, the namelist and streams fields can be modified in the user config yaml.

Finally, the `forecast` step runs the MPAS `atomsphere` executable.  If you want to add additional physics, you would add them in the physics field of the atmosphere namelist user config (see below).

### User Config yaml

Your user config (e.g. <your_name>.yaml) is how you update the default configuration with different settings.  Rather than going through and changing all of the different namelist and streams files that the MPAS Model produces, you only need to create and update the single user config file in the `ush` directory.  The file itself can be as simple as:
```
user:
  experiment_dir: /path/to/exp/dir
  platform: jet
platform:
  account: wrfruc
```
To update additional fields, you add the nested structure from `default_config.yaml` with the additional information.  For example, to modify the physics for the `atmosphere` executable to include Thompson microphysics, you would add the following to the user config yaml:
```
forecast:
  mpas:
    namelist:
      update_values:
        physics:
          config_microp_scheme = 'mp_thompson'
```

## Generate the Experiment

Prior to running the experiment, you must run the command `source load_wflow_modules.sh <plaform>` from the `mpas_app` directory. 

When you have a completed user config yaml, you can run the experiment_gen python script to generate the MPAS experiment:

`python experiment_gen.py <user_config.yaml>`

This will create an experiment directory with your `experiment.yaml` file, which contains the user modifications to the default yaml.  The experiment directory also contains a Rocoto XML file, which is ready to use with the command `rocotorun -w rocoto.xml -d rocoto.db`. You will have to iterately run this command until all steps have been completed. You can check the status of these steps by running `rocotostat -w rocoto.xml -d rocoto.db`.

Logs are populated for each of the different tasks in the workflow, and `workflow.log` contains the submission and completion statuses in text format.

## convert_mpas

To remap the model output to a lat/lon grid you can copy the `convert_mpas` executable to the directory with the model output:

`cp /lfs4/BMC/wrfruc/jderrico/mpas/exec/convert_mpas`

The `convert_mpas` executable requires an additional `include_fields` file and a `target_domain` file, more information can be found [here](https://github.com/mgduda/convert_mpas). 
