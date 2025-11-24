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

Archiving and Scrubbing
-----------------------

For any experiment of non-trivial size, automatically scrubbing the data is a good practice.
Presently, archiving and scrubbing must be used at the same time; this may be changed in a future release.
The reason scrubbing can't be run alone is that the workflow has no way to determine when you're
done with the data, except by archiving it.

To enable both archiving and scrubbing, add these lines:

.. code-block: yaml
   user:
     hpss_archive_dir: /a/path/on/hpss
     workflow_blocks:
       - archiving.yaml
       - scrubbing.yaml
  

You must replace ``/a/path/on/hpss`` with a valid path on an HPSS archiving system.
The scripts will use ``hsi`` and ``htar`` to write the data. If the directory doesn't exist,
the scripts will try to create it.

Archives are split by purpose. In these scripts, ``{CYCLE_YMDH}`` corresponds to the cycle date and time in ten digits; November 14, 2025 at 18:00 UTC would be 2025091418. The ``{FORECAST_YMD}` corresponds to the forecast date as eight digits; November 14, 2025 would be 20250914.

- ``{CYCLE_YMDH}-upp.tar`` - All grib files output by UPP and all small control files input to it. Excludes the combined grib since that is simply the concatenation of UPP output.
- ``{CYCLE_YMDH}-mpassit-{FORECAST_YMD}.tar`` - All mpassit files from forecast lead times on a given day. This is split by day because of limitations of HTAR.
- ``init*.nc`` - Not an archive; it is copied directly due to limitations of HTAR. This is the initial state from the forecast directory.
- ``init*.nc.md5`` - An md5sum of the init file.

Archiving (see ``parm/wflow/archiving.yaml``) is split into one job per archive:

- task ``archive_upp`` - archives UPP output to ``{CYCLE_YMDH}-upp.tar``
- metatask of ``archive_mpassit_dayN`` - archives mpassit output to ``{CYCLE_YMDH}-mpassit-{FORECAST_YMD}.tar``
- task ``archive_init`` - archives the init file from the forecast directory and calculates its md5sum

Scrubbing (see ``parm/wflow/scrubbing.yaml``) is split by file purpose:

- task ``scrub_forecast`` - Deletes all diag, history, and restart files from the forecast directory.
- task ``scrub_mpas_ics`` - Deltes the mpas_ics directory.
- task ``scrub_mpassit`` - Deletes the mpassit directories.
- task ``scrub_init`` - Deletes the init file from the forecast directory.

To disable scrubbing steps, use the ``!remove`` feature. For example, this disables scrubbing the forecast directory:

.. code-block: yaml
   workflow:
     tasks:
       task_scrub_forecast: !remove

See ``parm/wflow/scrubbing.yaml`` for a list of tasks.

Removing archiving steps has two steps. First, use ``!remove`` to remove tasks (see ``parm/wflow/archiving.yaml`` for a list). Then edit ``parm/wflow/scrubbing.yaml`` to remove any dependencies on the task.
