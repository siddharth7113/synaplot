"""Sphinx configuration."""

import sys
from importlib.metadata import version as get_version
from pathlib import Path

# The directives that draw the diagrams in these pages.
sys.path.insert(0, str(Path(__file__).parent / "_ext"))

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
    "synaplot_docs",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "_gallery", "_ext"]

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
# Link to a heading on another page by its text.
myst_heading_anchors = 3

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

# pydantic writes its field constraints into the annotations, and autodoc reads
# them as if they were types to link to. There is nothing to link to, and the
# constraint is already in the field's description.
nitpick_ignore_regex = [
    ("py:class", r"annotated_types\..*"),
    ("py:class", r"(ge|le|gt|lt|min_length|max_length)=.*"),
    ("py:class", r"PydanticUndefined"),
    ("py:class", r"SerializeAsAny"),
    # A numpydoc return type such as "dict of str to type of Layer" describes a
    # mapping in words. Napoleon tries to link the words after "of".
    ("py:class", r".+ to .+"),
    # The Python domain resolves a bare class name against the module it is
    # written in, and pathlib.Path is only findable by its full name.
    ("py:class", r"Path"),
]
