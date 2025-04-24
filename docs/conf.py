# See https://www.sphinx-doc.org/en/master/usage/configuration.html

import datetime as dt
import sys
from pathlib import Path

sys.path.insert(0, Path("../src").absolute())

autoclass_content = "both"
autodoc_mock_imports = []
autodoc_typehints = "description"
copyright = str(dt.datetime.now(tz=dt.timezone.utc).year)
extensions = ["sphinx.ext.autodoc", "sphinx.ext.extlinks", "sphinx.ext.intersphinx"]
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
user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
version = "0.0.0"

extlinks = {}


def setup(app):
    app.add_css_file("custom.css")
