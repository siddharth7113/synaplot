"""Checks that the package is installed and ships its LaTeX styles."""

from importlib.resources import files

import synaplot

STYLE_FILES = [
    "synaplot-ball.sty",
    "synaplot-box.sty",
    "synaplot-rightbandedbox.sty",
]


def test_version_is_readable():
    assert synaplot.__version__


def test_style_files_ship_with_the_package():
    styles = files("synaplot.latex") / "styles"
    for name in STYLE_FILES:
        assert (styles / name).is_file(), f"{name} is missing from the wheel"


def test_style_files_namespace_their_macros():
    r"""Checks that no style leaks a macro into the document that loads it.

    The styles these were derived from stored their keys in bare macro names
    such as ``\caption`` and ``\fill``, which redefined those commands in any
    document that loaded them. Every stored key uses the ``\sy@`` prefix.
    """
    styles = files("synaplot.latex") / "styles"
    for name in STYLE_FILES:
        source = (styles / name).read_text(encoding="utf-8")
        for line in source.splitlines():
            if "/.store" in line:
                target = line.split("in=")[-1].strip().rstrip(",")
                assert target.startswith("\\sy@"), (
                    f"{name} stores a key in {target}, which is not namespaced"
                )
