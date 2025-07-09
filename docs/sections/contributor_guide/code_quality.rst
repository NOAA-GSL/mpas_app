Code Quality
============

Several ``make`` targets are available for use in an activated ``mpas_app`` development environment:

* ``make docs`` to build the HTML documentation (see :doc:`Documentation <documentation>`).
* ``make format`` to format Python code and docstrings with :ruff:`ruff <>`.
* ``make lint`` to lint Python code with :ruff:`ruff <>`.
* ``make regtest`` to run the :ref:`regtests`.
* ``make systest`` to run the :ref:`systests`.
* ``make test`` to run the linter, typechecker, and unit tests.
* ``make typecheck`` to typecheck Python code with :mypy:`mypy <>`.
* ``make unittest`` to run the unit tests and report coverage with :pytest:`pytest <>` and :coverage:`coverage <>`.

Configuration for these tools is provided by the file ``pyproject.toml`` in the repo root.

Code should be formatted and tested periodically during the development process. A useful idiom is to run ``make format && make test`` to format the code and run all basic tests, which is equivalent to executing the ``format``, ``lint``, ``typecheck``, and ``unittest`` targets. The order is intentional:

* ``format`` will complain about certain kinds of syntax errors that would cause all the remaining code-quality tools to fail (and that could change line numbers reported by other tools, if it ran after them).
* ``lint`` provides a good first check for obvious errors and anti-patterns in the code.
* ``typecheck`` offers a more nuanced look at interfaces between functions, methods, etc. and may spot issues missed by the linter.
* ``unittest`` provides higher-level semantic-correctness checks once code syntax and typing is deemed correct.

All the above tests are executed by the CI system against PRs, so be sure that code is formatted and that tests pass locally.

The ``mpas_app`` repository has standardized 100% unit-test coverage, enforced by ``make unittest`` and its configuration in ``pyproject.toml``. Please help maintain this high standard.

.. _regtests:

Regression Tests
----------------

Coming soon.

.. _systests:

System Tests
------------

Coming soon.
