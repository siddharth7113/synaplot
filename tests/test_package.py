"""Checks that the package is installed and ships its LaTeX styles."""

from importlib.resources import files

import synaplot


def style_files():
    """Return every style that ships with the package.

    Read from the directory rather than listed here, so a style added to the
    package is tested without anything being kept up to date by hand.
    """
    styles = files("synaplot.latex") / "styles"
    return sorted(entry for entry in styles.iterdir() if entry.name.endswith(".sty"))


def test_version_is_readable():
    assert synaplot.__version__


def test_style_files_ship_with_the_package():
    found = style_files()
    assert found, "no styles were packaged, so no diagram can be drawn"
    for style in found:
        assert style.is_file()


def test_style_files_namespace_their_macros():
    r"""Checks that no style leaks a macro into the document that loads it.

    The styles these were derived from stored their keys in bare macro names
    such as ``\caption`` and ``\fill``, which redefined those commands in any
    document that loaded them. Every stored key uses the ``\sy@`` prefix.
    """
    for style in style_files():
        source = style.read_text(encoding="utf-8")
        for line in source.splitlines():
            if "/.store" in line:
                target = line.split("in=")[-1].strip().rstrip(",")
                assert target.startswith("\\sy@"), (
                    f"{style.name} stores a key in {target}, which is not namespaced"
                )
