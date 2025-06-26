Developer Setup
===============

MPAS App installs and manages its own conda installation in the ``conda/`` subdirectory of the ``mpas_app`` git clone root. To get started, run:

.. code-block:: bash

   make devenv
   source conda/etc/profile.d/conda.sh
   source docs/install-deps # if developing documentation
   conda activate mpas_app

After initial installation, the ``mpas_app`` environment can be re-activated in a fresh shell with the command:

.. code-block:: text

   source conda/etc/profile.d/conda.sh && conda activate mpas_app

.. note:: A conda installation may require several gigabytes of disk space and may not be appropriate for HPC home directories with small quotas. Consider cloning ``mpas_app`` somewhere with a sufficiently high quota or available disk space.
