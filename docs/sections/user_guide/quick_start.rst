CONUS 3km Quick Start Guide
---------------------------

1. On Hera or Jet, clone the app's ``main`` branch and navigate to its directory:

   .. code-block:: bash

      git clone https://github.com/NOAA-GSL/mpas_app.git --recursive
      cd mpas_app

2. Build the model and components:

   .. code-block:: bash

      ./build.sh -p <platform>

3. Load the ``mpas_app`` conda environment:

   .. code-block:: bash

      source load_wflow_modules.sh <platform>

4. Create your user yaml in the ``ush`` directory. The file itself can be as simple as:

   .. code-block:: yaml

      user:
        experiment_dir: /path/to/exp/dir
        platform: jet
      platform:
        account: wrfruc

5. Generate the experiment:

   .. code-block:: bash

      cd ush
      ./experiment_gen.py workflows/3km_conus.yaml workflows/conus.<platform>.yaml <your_user_yaml.yaml>

This generates an experiment directory at the path specified in your user YAML that contains a Rocoto XML file, which is ready to use.

