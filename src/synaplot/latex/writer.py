"""Turns a diagram into LaTeX source."""

from __future__ import annotations

from functools import lru_cache
from importlib.resources import files
from typing import TYPE_CHECKING

from synaplot.core.base import DrawContext
from synaplot.core.diagram import Bend, ConnectionStyle
from synaplot.core.geometry import Anchor
from synaplot.core.theme import color_macro

if TYPE_CHECKING:
    from synaplot.core.diagram import Connection, Diagram

# Libraries the drawing needs: quotes for the labels along a box edge, 3d for
# the plane an input image is drawn on, arrows.meta for the arrowheads, and
# positioning for the anchors.
TIKZ_SETUP = r"""
\usetikzlibrary{quotes,arrows.meta,positioning,3d}
""".strip()

# Definitions the connections rely on: \syArrow and \syCopyArrow draw the
# arrowhead placed partway along a line, and syConnection and syCopyConnection
# are the line styles themselves. EDGE is a placeholder that preamble() swaps
# for the theme's edge color.
ARROW_STYLES = r"""
\newcommand{\syArrow}{%
    \tikz \draw[-Stealth,line width=0.8mm,draw=EDGE] (-0.3,0) -- ++(0.3,0);}
\newcommand{\syCopyArrow}{%
    \tikz \draw[-Stealth,line width=0.8mm,draw=EDGE] (-0.3,0) -- ++(0.3,0);}
\tikzset{
    syConnection/.style={
        ultra thick, draw=EDGE, opacity=0.7,
        every node/.style={sloped,allow upside down}},
    syCopyConnection/.style={
        ultra thick, draw=EDGE, opacity=0.7,
        every node/.style={sloped,allow upside down}},
    syEdge/.style={draw=EDGE, opacity=0.35, line width=0.2mm},
}
""".strip()


@lru_cache(maxsize=1)
def style_source() -> str:
    """Return the TikZ style definitions that ship with the package.

    The definitions are read from the package and returned as text so they can
    be written straight into a document. A document that carries them needs no
    style files beside it, which is what lets a diagram compile from any
    directory and paste into a service such as Overleaf.

    Returns
    -------
    str
        The contents of every style file, one after another. Adding a style to
        the styles directory is enough to include it; the files define
        independent pics, so they are read in name order for a stable result.
    """
    styles = files("synaplot.latex") / "styles"
    sources = sorted(
        (entry.name, entry.read_text(encoding="utf-8"))
        for entry in styles.iterdir()
        if entry.name.endswith(".sty")
    )
    return "\n\n".join(
        "\n".join(
            line
            for line in text.splitlines()
            if not line.startswith("\\ProvidesPackage")
        ).strip()
        for _, text in sources
    )


def preamble(diagram: Diagram) -> str:
    """Return the LaTeX that must appear before the drawing.

    Parameters
    ----------
    diagram
        The diagram whose theme supplies the colors.

    Returns
    -------
    str
        TikZ library imports, the style definitions, the theme colors, and the
        arrow styles used by connections.
    """
    arrows = ARROW_STYLES.replace("EDGE", f"\\{color_macro('edge')}")
    return "\n\n".join(
        [TIKZ_SETUP, style_source(), diagram.theme.macro_definitions(), arrows]
    )


def connection_to_tikz(
    connection: Connection, roof: float, diagram: Diagram | None = None
) -> str:
    r"""Return the TikZ that draws one arrow.

    Parameters
    ----------
    connection
        The arrow to draw.
    roof
        Height of the tallest layer in the diagram, measured from the axis. A
        skip arrow runs above this, so it clears every layer it passes.
    diagram
        The diagram being drawn. A full connection needs it to find how many
        nodes each end has.

    Returns
    -------
    str
        One or more TikZ statements.
    """
    source, target = connection.source, connection.target
    if connection.style is ConnectionStyle.FULL:
        return _full_connection(connection, diagram)

    if connection.style is ConnectionStyle.FORWARD:
        start = (connection.source_anchor or Anchor.EAST).value
        end = (connection.target_anchor or Anchor.WEST).value
        return (
            f"\\draw [syConnection] ({source}-{start}) "
            f"-- node {{\\syArrow}} ({target}-{end});"
        )

    if connection.style is ConnectionStyle.BYPASS:
        return _bypass(connection)

    if connection.style is ConnectionStyle.ELBOW:
        # TikZ turns the corner itself: -| goes across and then down, and |-
        # goes down and then across.
        start = (connection.source_anchor or Anchor.EAST).value
        end = (connection.target_anchor or Anchor.WEST).value
        corner = "-|" if connection.bend is Bend.ACROSS_THEN_DOWN else "|-"
        return (
            f"\\draw [syConnection] ({source}-{start}) "
            f"{corner} node[near end] {{\\syArrow}} ({target}-{end});"
        )

    # Both ends rise to the same height, so the run between them is level. Using
    # each layer's own height instead would slant the run whenever two layers of
    # different heights are connected.
    level = _format(roof * connection.height)
    top_source = f"{source}-{target}-roof-{source}"
    top_target = f"{source}-{target}-roof-{target}"
    return "\n".join(
        [
            f"\\coordinate ({top_source}) at ({source}-north |- 0,{level});",
            f"\\coordinate ({top_target}) at ({target}-north |- 0,{level});",
            f"\\draw [syCopyConnection] ({source}-north) -- ({top_source})",
            f"    -- node {{\\syCopyArrow}} ({top_target}) -- ({target}-north);",
        ]
    )


#: Which way a bypass steps out, per anchor it leaves from.
_STEP_OUT = {
    Anchor.EAST: (1, 0),
    Anchor.WEST: (-1, 0),
    Anchor.NORTH: (0, 1),
    Anchor.SOUTH: (0, -1),
}


def _bypass(connection: Connection) -> str:
    """Return an arrow that steps aside, runs past, and comes back in.

    Raises
    ------
    ValueError
        If the arrow leaves from an anchor with no clear direction to step out
        in, such as a corner.
    """
    start = connection.source_anchor or Anchor.EAST
    end = connection.target_anchor or start
    if start not in _STEP_OUT:
        sides = ", ".join(anchor.value for anchor in _STEP_OUT)
        raise ValueError(f"a bypass must leave from one of {sides}, not {start.value}")
    across, up = _STEP_OUT[start]
    step = (
        f"({_format(across * connection.clearance)},"
        f"{_format(up * connection.clearance)})"
    )
    # Having stepped sideways, come back on the other axis first, so the arrow
    # meets the target square on rather than at a slant.
    corner = "|-" if across else "-|"
    return (
        f"\\draw [syConnection] ({connection.source}-{start.value}) -- ++{step}\n"
        f"    {corner} node[near end] {{\\syArrow}} ({connection.target}-{end.value});"
    )


def _full_connection(connection: Connection, diagram: Diagram | None) -> str:
    """Return a line from every node of one layer to every node of the other.

    Raises
    ------
    ValueError
        If either layer is not drawn as separate nodes, since there would be
        nothing for the lines to join.
    """
    if diagram is None:
        raise ValueError("a full connection can only be drawn as part of a diagram")
    source, target = connection.source, connection.target
    starts = diagram[source].node_names()
    ends = diagram[target].node_names()
    for name, nodes in ((source, starts), (target, ends)):
        if not nodes:
            raise ValueError(
                f"{name!r} is not drawn as separate nodes, so it cannot take a "
                f"full connection; use a dense layer at both ends"
            )
    return "\n".join(
        f"\\draw [syEdge] ({source}-{start}) -- ({target}-{end});"
        for start in starts
        for end in ends
    )


def _format(value: float) -> str:
    """Format a number for LaTeX, dropping a trailing ``.0``.

    Parameters
    ----------
    value
        The number to format.

    Returns
    -------
    str
        The number without a redundant decimal part.
    """
    return str(int(value)) if value == int(value) else repr(round(value, 4))


def diagram_to_tikz(diagram: Diagram) -> str:
    """Return the body of the ``tikzpicture`` that draws a diagram.

    Parameters
    ----------
    diagram
        The diagram to draw.

    Returns
    -------
    str
        TikZ statements, without the surrounding environment.
    """
    scale = diagram.scale.value
    blocks = [
        layer.to_tikz(DrawContext(theme=diagram.theme, scale=scale, attach=attach))
        for layer, attach in diagram.placements()
    ]
    roof = max((layer.half_height(scale) for layer in diagram.layers), default=0.0)
    blocks += [connection_to_tikz(c, roof, diagram) for c in diagram.connections]
    return "\n\n".join(blocks)


def diagram_to_tex(diagram: Diagram, *, standalone: bool = True) -> str:
    """Return a LaTeX document that draws a diagram.

    Parameters
    ----------
    diagram
        The diagram to draw.
    standalone
        Whether to wrap the drawing in a document that compiles on its own.
        Pass ``False`` to get the preamble and the drawing as two parts to
        paste into a document that already exists.

    Returns
    -------
    str
        LaTeX source.
    """
    picture = (
        f"\\begin{{tikzpicture}}\n{diagram_to_tikz(diagram)}\n\\end{{tikzpicture}}"
    )
    if not standalone:
        return f"{preamble(diagram)}\n\n{picture}\n"
    return "\n\n".join(
        [
            "\\documentclass[border=8pt, multi, tikz]{standalone}",
            "\\usepackage{graphicx}",
            preamble(diagram),
            f"\\begin{{document}}\n{picture}\n\\end{{document}}\n",
        ]
    )
