Building and Running the MPAS App
=================================

Getting Started
---------------

The ``mpas_app`` default is currently set to run on a 3-km CONUS mesh using GFS initial and lateral boundary conditions. To get started, clone the app and navigate to its directory:

.. code-block:: bash

   git clone https://github.com/NOAA-GSL/mpas_app.git --recursive
   cd mpas_app

When switching branches or if you forget the ``--recursive`` flag, run:

.. code-block:: bash

   git submodule update --init --recursive

Building the Model
------------------

Jet and Hera are the only platforms fully supported on the ``main`` branch. To run the default build script:

.. code-block:: bash

   ./build.sh -p <platform>

The app is partially supported on Ursa for the HFIP 2025 experiment configuration.

To view all build options, run:

.. code-block:: bash

   ./build.sh -h

This builds the MPAS-Model (based on MPAS release version ``8.2.2``) and installs Miniconda inside the local clone. The ``ungrib`` conda environment includes a pre-built WPS Ungrib package. The full build may take up to an hour.

Default Configuration
---------------------

``default_config.yaml`` is located in the ``ush`` directory. It is structured with top-level blocks representing MPAS App workflow steps. Subsections follow `UW Tools YAML <https://uwtools.readthedocs.io/en/main/sections/user_guide/yaml/components/index.html>`_ for specific drivers.

The ``user:`` section contains common high-level config options like cycle dates, platform, and tasks to run.

- ``get_ics_data`` and ``get_lbcs_data`` define retrieval of data from AWS.
- ``prepare_grib_ics`` and ``prepare_grib_lbcs`` define GRIB processing with `ungrib <https://uwtools.readthedocs.io/en/main/sections/user_guide/yaml/components/ungrib.html>`_.
- ``create_ics`` and ``create_lbcs`` define `mpas_init <https://uwtools.readthedocs.io/en/main/sections/user_guide/yaml/components/mpas_init.html>`_ setup.
- ``forecast`` defines ``atmosphere_model`` config and can be extended for additional physics options.
- ``post`` includes tasks like GRIB combination, ``MPASSIT``, and `UPP <https://uwtools.readthedocs.io/en/main/sections/user_guide/yaml/components/upp.html>`_ post-processing.

All settings can be overridden via a user-provided YAML matching the structure of ``default_config.yaml``.

User Config YAML
----------------

You can provide a user configuration YAML (e.g. ``<your_name>.yaml``) during setup to override default values.

Minimal example:

.. code-block:: yaml

   user:
     experiment_dir: /path/to/exp/dir
     platform: jet
   platform:
     account: wrfruc

To modify the forecast physics (e.g. use Thompson microphysics):

.. code-block:: yaml

   forecast:
     mpas:
       namelist:
         update_values:
           physics:
             config_microp_scheme: mp_thompson

For more YAML documentation, see `uwtools <https://uwtools.readthedocs.io/en/main/sections/user_guide/yaml/index.html>`_.

To remove tasks from the workflow:

.. code-block:: yaml

   workflow:
     tasks:
       task_get_lbcs_data: !remove
       task_mpas_lbcs: !remove

Generating the Experiment
-------------------------

Activate the environment from the ``mpas_app/`` directory:

.. code-block:: bash

   source load_wflow_modules.sh <platform>

Then from ``mpas_app/ush/``, run:

.. code-block:: bash

   cd ush
   ./experiment_gen.py workflows/3km_conus.yaml workflows/conus.<platform>.yaml [optional.yaml] user_config.yaml

Later YAMLs take precedence over earlier ones. The resulting experiment directory contains:

- ``experiment.yaml`` with final config
- ``rocoto.xml`` (ready for ``rocotorun``)

To run the experiment:

.. code-block:: bash

   rocotorun -w rocoto.xml -d rocoto.db

Re-run this until all steps are complete. Check status:

.. code-block:: bash

   rocotostat -w rocoto.xml -d rocoto.db

Task logs are saved individually, with an overall status in ``workflow.log``.

Post-Processing
---------------

``MPASSIT`` and ``UPP`` are included as submodules on Jet and Hera. Configure them via the user YAML using the same nested structure as above.
