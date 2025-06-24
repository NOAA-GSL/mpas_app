Documentation
=============

Locally Building and Previewing Documentation
---------------------------------------------

To locally build the docs:

#. Create and activate a development environment as described in the :doc:`Developer Setup <developer_setup>` section.
#. From the clone root, install the required additional packages: ``. docs/install-deps``
#. Build the docs: ``make docs``

The ``make docs`` command will build the docs under ``docs/build/html``, after which you can preview them in your web browser at the URL

.. code-block:: text

   file://<filesystem-path-to-your-clone>/docs/build/html/index.html

After making and saving changes, re-run ``make docs`` and refresh your browser.

If, at some point, you remove and recreate the ``mpas_app`` development environment, you will need to re-run ``. install-deps`` in the new environment. Until then, the installed doc packages will persist and support docs generation.

Viewing Online Documentation
----------------------------

Online documentation generation and hosting for ``mpas_app`` is provided by :rtd:`Read the Docs <>`. Click *View docs* to view the official docs for the project.

Docs are also built and temporarily published for PRs to this repo. To view, visit the :rtd:`builds page <builds>`, click the latest build corresponding to your PR number, then click *View docs*.

Documentation Guidelines
------------------------

Please follow these guidelines when contributing to the documentation:

* Keep formatting consistent across pages. Update all pages when better ideas are discovered. Otherwise, follow the conventions established in existing content.
* Ensure that the ``make docs`` command completes with no errors or warnings.
* If the link-check portion of ``make docs`` reports that a URL is ``permanently`` redirected, update the link in the docs to use the new URL. Non-permanent redirects may be left as-is.
* Do not manually wrap lines in the ``.rst`` files. Insert newlines only as needed to achieve correctly formatted HTML, and let HTML wrap long lines and/or provide a scrollbar.
* Use one blank line between documentation elements (headers, paragraphs, code blocks, etc.) unless additional lines are necessary to achieve correctly formatted HTML.
* Remove all trailing whitespace, except where inserted by dynamic content generation (don't fight the tooling).
* In general, avoid pronouns like "we" and "you". (Using "we" may be appropriate when synonymous with "The MPAS App Team", when the context is clear.) Prefer direct, factual statements about what the code does, requires, etc.
* Use the `Oxford Comma <https://en.wikipedia.org/wiki/Serial_comma>`_.
* Follow the :rst:`RST Sections <basics.html#sections>` guidelines, underlining section headings with ``=`` characters, subsections with ``-`` characters, and subsubsections with ``^`` characters. If a further level of refinement is needed, indented and/or bulleted lists, as subsections marked with  ``"`` are nearly indistinguishable from those marked with ``^``.
* In [[sub]sub]section titles, capitalize all "principal" words. In practice this usually means all words but articles (a, an, the), logicals (and, etc.), and prepositions (for, of, etc.). Always fully capitalize acronyms (e.g., YAML).
* Never capitalize proper names when their owners do not (e.g., write `"pandas" <https://pandas.pydata.org/>`_, not "Pandas", even at the start of a sentence) or when referring to a software artifact (e.g., write ``numpy`` when referring to the library, and "NumPy" when referring to the project).
* When referring to YAML constructs, `block` refers to an entry whose value is a nested collection of key/value pairs, while `entry` refers to a single key/value pair.
* When using the ``.. code-block::`` directive, align the actual code with the word ``code``. Also, when ``.. code-block::`` directives appear in bulleted or numbered lists, align them with the text following the space to the right of the bullet/number. For example:

  .. code-block:: text

     * Lorem ipsum

       .. code-block:: python

          n = 42

  or

  .. code-block:: text

     #. Lorem ipsum

        .. code-block:: python

           n = 42
