RRFS Forecast Ensemble Quick Start Guide
----------------------------------------

1. Clone the app's ``rrfs_ensemble`` branch:

   .. code-block:: bash

      git clone https://github.com/NOAA-GSL/mpas_app.git -b rrfs_ensemble --recursive
      cd mpas_app

   This branch is kept in sync with the mpas_app ``main`` branch, but points to the RRFS development branch in https://github.com/RRFSx/MPAS-Model.

2. Build the model and components:

   .. code-block:: bash

      ./build.sh -p <platform>

3. Load the ``mpas_app`` conda environment:

   .. code-block:: bash

      source load_wflow_modules.sh <platform>

4. Create your user YAML in the ``ush`` directory. The file can be structured to overwrite any settings in the app, but can be as simple as:

   .. code-block:: yaml

      user:
        experiment_dir: /path/to/exp/dir
        platform: ursa
      platform:
        account: wrfruc

5. Generate the experiment:

   .. code-block:: bash

      cd ush
      ./experiment_gen.py workflows/ensemble_wflow.yaml <your_user_yaml.yaml>

This generates an experiment directory at the ``experiment_dir`` path specified in your user YAML that contains a Rocoto XML file, which is ready to use.


Configuring the RRFS Ensemble
-----------------------------

The ``workflows/ensemble_wflow.yaml`` defaults to a 2-member, RRFS-DA-ensemble-initialized ensemble with GFS lateral boundary conditions. The forecast configuration otherwise uses the base namelist used by RRFS.

All modifications meant for scientific experimentation can be made in the user's YAML. Changes meant for contribution to the code base may be made by adding new ``ush/workflows`` YAML files, or by modifying existing ones.

YAML configs passed to the ``ush/experiment_gen.py`` increase in precedence from left to right, where higher precedence settings will override those set in the ``default_config.yaml`` or those provided earlier in the list. To override a setting, simply create the desired key/value pair mirroring that in the original configuration file. Defaults loaded in the ``ush/experiment_gen.py`` include the ``ush/default_config.yaml``, the ``parm/machines/<platform>.yaml``, and the relevant sets of ``parm/wflow`` YAMLs.

Changing Ensemble Size and Forecast Length
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The following is an example of settings could be used in the user YAML in addition to the required settings to change the basic ensemble configuration:

    .. code-block:: yaml

       user:
         ensemble_size: 4
       forecast:
         mpas:
           length: 48

Any other existing settings can be similarly changed.

Stochastic Perturbations
^^^^^^^^^^^^^^^^^^^^^^^^

Stochastic perturbation support is being added in `MPAS PR #239 <https://github.com/ufs-community/MPAS-Model/pull/239>`_. Assuming only namelist changes from that PR are needed in the final implementation, the following section could be added to modify the namelist once, but generate a different seed for each member at run time. This solution leverages the fact that the MPAS App ensemble configuration has the ``MEM`` environment variable available to each member, and it's an integer.

    .. code-block:: yaml

       forecast:
         mpas:
           namelist:
             update_values:
               stoch_physics:
                 do_sppt: true
                 do_skeb: false
                 config_spptint: 0
                 config_sppt_1: 0.8
                 config_sppt_2: 0.0
                 config_sppt_3: 0.0
                 config_sppt_tau_1: 21600
                 config_sppt_tau_2: 86400
                 config_sppt_tau_3: 21600
                 config_sppt_lscale_1: 450000
                 config_sppt_lscale_2: 1000000
                 config_sppt_lscale_3: 2000000
                 config_sppt_logit: true
                 config_sppt_sfclimit: true
                 config_iseed_sppt1: '{{ cycle.strftime("%Y%m%d%H") + "MEM" | env }}'
                 config_iseed_sppt2: '0'
                 config_iseed_sppt3: '0'
                 config_sppt_hgt_top1: 15000
                 config_sppt_hgt_top2: 27000
                 config_stochini: false

