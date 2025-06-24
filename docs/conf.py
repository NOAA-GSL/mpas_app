# See https://www.sphinx-doc.org/en/master/usage/configuration.html

# ruff: noqa: INP001

import datetime as dt
import sys
from pathlib import Path

sys.path.insert(0, str(Path("../src").absolute()))

autoclass_content = "both"
autodoc_mock_imports: list = []
autodoc_typehints = "description"
copyright = str(dt.datetime.now(tz=dt.timezone.utc).year)  # noqa: A001
extensions = ["sphinx.ext.autodoc", "sphinx.ext.extlinks", "sphinx.ext.intersphinx"]
extlinks: dict = {
    "coverage": ("https://coverage.readthedocs.io/en/7.3.4/%s", "%s"),
    "miniforge": ("https://github.com/conda-forge/miniforge/%s", "%s"),
    "mpas_app": ("https://github.com/noaa-gsl/mpas_app/%s", "%s"),
    "mypy": ("https://mypy.readthedocs.io/en/stable/%s", "%s"),
    "pytest": ("https://docs.pytest.org/en/7.4.x/%s", "%s"),
    "ruff": ("https://docs.astral.sh/ruff/%s", "%s"),
}
extlinks_detect_hardcoded_links = True
html_logo = str(Path("static", "logo.png"))
html_static_path = ["static"]
html_theme = "sphinx_rtd_theme"
intersphinx_mapping = {"python": ("https://docs.python.org/3", None)}
nitpick_ignore_regex = {("py:class", ".*")}  # comment out to see types Sphinx can't create links to
numfig = True
numfig_format = {"figure": "Figure %s"}
project = "MPAS App"
release = "0.0.0"
version = "0.0.0"

def setup(app):
    app.add_css_file("custom.css")
