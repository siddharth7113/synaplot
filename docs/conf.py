"""Sphinx configuration."""

from importlib.metadata import version as get_version

project = "synaplot"
copyright = "2026, Siddharth"
author = "Siddharth"
release = get_version("synaplot")
version = release

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "myst_parser",
    "sphinx_copybutton",
    "sphinx_design",
]

templates_path = ["_templates"]
exclude_patterns = ["_build"]

autosummary_generate = True
autodoc_typehints = "description"
autodoc_member_order = "bysource"
napoleon_numpy_docstring = True
napoleon_google_docstring = False

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "pydantic": ("https://docs.pydantic.dev/latest", None),
}

myst_enable_extensions = ["colon_fence", "deflist"]

html_theme = "pydata_sphinx_theme"
html_title = "synaplot"
html_static_path = ["_static"]
html_theme_options = {
    "github_url": "https://github.com/siddharth7113/synaplot",
    "logo": {
        "image_light": "_static/wordmark.svg",
        "image_dark": "_static/wordmark-dark.svg",
        "alt_text": "synaplot",
    },
    "navbar_end": ["theme-switcher", "navbar-icon-links"],
    "show_prev_next": False,
}

# Warn about every cross-reference that cannot be resolved. The docs build runs
# with -W, so a broken reference fails CI.
nitpicky = True
