import os
import sys
sys.path.insert(0, os.path.abspath('../src'))

# -- Project information -----------------------------------------------------

project = 'AsciiDoc Parser'
copyright = '2026, Michael R. Bernstein'
author = 'Michael R. Bernstein'
release = '0.1.0'

# -- General configuration ---------------------------------------------------

extensions = [
    'sphinx_rtd_theme',
    'asciidoc_parser.sphinx_ext',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# -- Options for HTML output -------------------------------------------------

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

# -- Extension configuration --------------------------------------------------

# Our parser registers .adoc and .asciidoc suffixes automatically via setup()
