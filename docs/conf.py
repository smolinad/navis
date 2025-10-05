import os
import sys

# Add the repo root so Sphinx can find 'navis'
sys.path.insert(0, os.path.abspath("../"))

# -- Project information -----------------------------------------------------

project = "Navis"
copyright = ""
author = "EML 5808 - Spring 2025"
release = "0.1.0"

# -- General configuration ---------------------------------------------------

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",     # Support for Google/Numpy-style docstrings
    "sphinx.ext.viewcode",     # Adds "View Source" links to documentation
    "sphinx.ext.autosummary",  # Automatically generate summary tables
    "sphinx.ext.todo",         # Optional: allows .. todo:: directives
    "sphinx.ext.intersphinx",  # For linking to Python or other package docs
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- Options for HTML output -------------------------------------------------

html_theme = "shibuya"

html_static_path = ["_static"]

html_theme_options = {
  "github_url": "https://github.com/smolinad/navis"
}

html_context = {
    "source_type": "github",
    "source_user": "smolinad",
    "source_repo": "navis",
}

html_context = {
    "source_type": "github|gitlab|bitbucket",
    "source_user": "smolinad",
    "source_repo": "navis",
    "source_version": "main",  # Optional
    "source_docs_path": "/docs/",  # Optional
}

html_css_files = [
    'custom.css',
]

# -- Autodoc and Napoleon settings -------------------------------------------

autodoc_member_order = "bysource"
autosummary_generate = True
napoleon_google_docstring = True
napoleon_numpy_docstring = True

# -- Intersphinx -------------------------------------------------------------

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}

# -- Todo extension (optional) -----------------------------------------------

todo_include_todos = True
