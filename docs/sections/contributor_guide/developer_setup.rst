Developer Setup
===============

Create and Activate an MPAS App Developer Environment
-----------------------------------------------------

If an existing conda (:miniforge:`Miniforge<>` recommended) installation is available and writable, you may activate it and skip step 1.

#. Visit the :miniforge:`Miniforge releases page<releases/latest>` and download the ``Miniforge3-[os]-[architecture].sh`` installer appropriate to your system, for example ``Miniforge3-Linux-x86_64.sh``:

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

#. In a clone of the :mpas_app:`mpas_app repository<>`, create and activate the development environment.

   .. code-block:: text

      cd /to/your/mpas_app/clone
      make devenv
      conda activate mpas_app

If the above is successful, you will be in an ``mpas_app`` development environment, and your shell prompt should now be prefixed with ``(mpas_app)``. Type ``conda deactivate`` to deactivate the environment. You can remove the environment with the command ``make rmenv`` (or ``conda env remove -y -n mpas_app``).

Make Targets Available in a Development Environment
---------------------------------------------------

Several ``make`` targets are available for use In the ``mpas_app`` development environment:

- ``make docs`` to build the HTML documentation (see :doc:`Documentation <documentation>`).
- ``make format`` to format all Python code.
- ``make lint`` to run the linter.
- ``make regtest`` to run the regression tests.
- ``make systest`` to run system tests.
- ``make test`` to run the linter, typechecker, and unit tests.
- ``make typecheck`` to run the typechecker.
- ``make unittest`` to run the unit tests.

The code-formatting and quality checkers should be manually run periodically during the development process; a common idiom is to run ``make format && make test`` to format the code and run all basic checks. See :doc:`Code Quality <code_quality>` for details.
