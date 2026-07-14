import os
import sys

sys.path.insert(0, os.path.abspath("../src"))

from importlib.metadata import version as get_version

# -- Project information -----------------------------------------------------

project = "AsciiDoctrine"
copyright = "2026, Michael R. Bernstein"
author = "Michael R. Bernstein"
try:
    release = get_version("asciidoctrine")
except Exception:
    release = "0.1.0a8"

# -- General configuration ---------------------------------------------------

extensions = [
    "sphinx_rtd_theme",
    "asciidoctrine.sphinx_ext",
    "sphinx.ext.githubpages",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- Options for HTML output -------------------------------------------------

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]

# -- Extension configuration --------------------------------------------------

# Our parser registers .adoc and .asciidoc suffixes automatically via setup()
