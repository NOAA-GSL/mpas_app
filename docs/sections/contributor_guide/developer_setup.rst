Developer Setup
===============

If an existing conda (:miniforge:`Miniforge <>` recommended) installation is available and writable, activate it and skip step 1.

#. Visit the :miniforge:`Miniforge releases page <releases/latest>` and download the ``Miniforge3-[os]-[architecture].sh`` installer appropriate to the target system, for example ``Miniforge3-Linux-x86_64.sh``:

   .. code-block:: text

      wget <installer-url>
      bash <installer-filename> -bfp <installation-directory>
      rm <installer-filename>
      source <installation-directory>/etc/profile.d/conda.sh
      conda activate

   After the initial installation, this conda may be activated at any time with the command:

   .. code-block:: text

      source <installation-directory>/etc/profile.d/conda.sh && conda activate

   Note that a conda installation may require several gigabytes of disk space and may not be appropriate for HPC home directories with small quotas.

#. In a clone of the :mpas_app:`mpas_app repository <>`, create and activate the development environment.

   .. code-block:: text

      cd /to/the/mpas_app/clone
      make devenv
      conda activate mpas_app

If the above is successful, the ``mpas_app`` development environment will be activated, and the shell prompt should now be prefixed with ``(mpas_app)``. Type ``conda deactivate`` to deactivate the environment. You can remove the environment with the command ``make rmenv`` (or ``conda env remove -y -n mpas_app``).
