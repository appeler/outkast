"""Configuration file for the Sphinx documentation builder."""

from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import version from package metadata
try:
    from importlib.metadata import version as get_version

    release = get_version("outkast")
except ImportError:
    release = "unknown"

# Project information
project = "outkast"
copyright = f"{datetime.now().year}, Gaurav Sood, Suriyan Laohaprapanon"
author = "Gaurav Sood, Suriyan Laohaprapanon"

# Extensions
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    "sphinx.ext.githubpages",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# The theme to use for HTML and HTML Help pages.
html_theme = "furo"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]

# Create _static directory if it doesn't exist
os.makedirs(Path(__file__).parent / "_static", exist_ok=True)

# Auto-generate API documentation
autosummary_generate = True
autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": True,
    "special-members": "__init__",
}

# Napoleon settings for Google/NumPy style docstrings
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False

# Intersphinx mapping
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "pandas": ("https://pandas.pydata.org/docs/", None),
}

# HTML theme options (for Furo theme)
html_theme_options = {}

# HTML context
html_context = {
    "display_github": True,
    "github_user": "appeler",
    "github_repo": "outkast",
    "github_version": "master",
    "conf_py_path": "/docs/",
}
