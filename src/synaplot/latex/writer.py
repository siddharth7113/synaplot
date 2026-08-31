"""Turns a diagram into LaTeX source."""

from __future__ import annotations

from functools import lru_cache
from importlib.resources import files
from typing import TYPE_CHECKING

from synaplot.core.base import DrawContext, Layer
from synaplot.core.diagram import Bend, ConnectionStyle
from synaplot.core.geometry import Anchor
from synaplot.core.theme import color_macro

if TYPE_CHECKING:
    from synaplot.core.diagram import Connection, Diagram

# Libraries the drawing needs: quotes for the labels along a box edge, 3d for
# the plane an input image is drawn on, arrows.meta for the arrowheads, and
# positioning for the anchors. The background layer holds the lines a fully
# connected layer draws, so they pass behind the circles they join instead of
# across them.
TIKZ_SETUP = r"""
\usetikzlibrary{quotes,arrows.meta,positioning,3d}
\pgfdeclarelayer{syBackground}
\pgfsetlayers{syBackground,main}
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
    syHead/.style={-{Stealth[length=3.5mm,width=3mm]}},
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

    line, head = _arrowhead(connection, diagram)

    if connection.style is ConnectionStyle.FORWARD:
        start = (connection.source_anchor or Anchor.EAST).value
        end = (connection.target_anchor or Anchor.WEST).value
        return f"\\draw [{line}] ({source}-{start}) --{head} ({target}-{end});"

    if connection.style is ConnectionStyle.BYPASS:
        return _bypass(connection, line, head)

    if connection.style is ConnectionStyle.ELBOW:
        # TikZ turns the corner itself: -| goes across and then down, and |-
        # goes down and then across.
        start = (connection.source_anchor or Anchor.EAST).value
        end = (connection.target_anchor or Anchor.WEST).value
        corner = "-|" if connection.bend is Bend.ACROSS_THEN_DOWN else "|-"
        return f"\\draw [{line}] ({source}-{start}) {corner}{head} ({target}-{end});"

    # Both ends rise to the same height, so the run between them is level. Using
    # each layer's own height instead would slant the run whenever two layers of
    # different heights are connected.
    level = _format(roof * connection.height)
    top_source = f"{source}-{target}-roof-{source}"
    top_target = f"{source}-{target}-roof-{target}"
    line = line.replace("syConnection", "syCopyConnection")
    return "\n".join(
        [
            f"\\coordinate ({top_source}) at ({source}-north |- 0,{level});",
            f"\\coordinate ({top_target}) at ({target}-north |- 0,{level});",
            f"\\draw [{line}] ({source}-north) -- ({top_source})",
            f"    --{head.replace('syArrow', 'syCopyArrow')} ({top_target})"
            f" -- ({target}-north);",
        ]
    )


def _arrowhead(connection: Connection, diagram: Diagram | None) -> tuple[str, str]:
    """Return the line style and the arrowhead node for one arrow.

    An arrow into a flat layer ends in an arrowhead at the anchor. An arrow
    into a layer drawn as a volume carries its arrowhead partway along the
    line, because the anchor of a volume sits inside the shape, where an
    arrowhead is hidden. That is what PlotNeuralNet does, and it puts the head
    in the gap between two boxes, where there is room to see it.

    Returns
    -------
    tuple of (str, str)
        The style to draw the line with, and the node that carries the
        arrowhead. The node is empty when the head sits at the end of the line.
    """
    into_flat = diagram is not None and diagram[connection.target].flat
    if into_flat:
        return "syConnection,syHead", ""
    placement = "" if connection.style is ConnectionStyle.FORWARD else "[near end]"
    return "syConnection", f" node{placement} {{\\syArrow}}"


#: Which way a bypass steps out, per anchor it leaves from.
_STEP_OUT = {
    Anchor.EAST: (1, 0, 0),
    Anchor.WEST: (-1, 0, 0),
    Anchor.NORTH: (0, 1, 0),
    Anchor.SOUTH: (0, -1, 0),
    # Stepping out along the depth axis moves the arrow towards the reader or
    # away from them, which is where a drawing of feature maps has room. It is
    # how several arrows leaving one line reach a row of layers of their own.
    Anchor.NEAR: (0, 0, 1),
    Anchor.FAR: (0, 0, -1),
    # A corner steps out to the side it names. Two residual arrows can then
    # leave the same layer, one from the corner and one from the side, without
    # the second running back down the line the first came in on.
    Anchor.NORTHEAST: (1, 0, 0),
    Anchor.SOUTHEAST: (1, 0, 0),
    Anchor.NORTHWEST: (-1, 0, 0),
    Anchor.SOUTHWEST: (-1, 0, 0),
}

#: Which face a bypass comes back in on, per direction it stepped out in.
_SIDE = {
    (1, 0, 0): Anchor.EAST,
    (-1, 0, 0): Anchor.WEST,
    (0, 1, 0): Anchor.NORTH,
    (0, -1, 0): Anchor.SOUTH,
    (0, 0, 1): Anchor.NEAR,
    (0, 0, -1): Anchor.FAR,
}


def _bypass(connection: Connection, line: str, head: str) -> str:
    """Return an arrow that steps aside, runs past, and comes back in.

    Raises
    ------
    ValueError
        If the arrow leaves from an anchor with no clear direction to step out
        in, such as the centre of the layer.
    """
    start = connection.source_anchor or Anchor.EAST
    if start not in _STEP_OUT:
        sides = ", ".join(anchor.value for anchor in _STEP_OUT)
        raise ValueError(f"a bypass must leave from one of {sides}, not {start.value}")
    across, up, out = _STEP_OUT[start]
    # An arrow that left from a corner comes back in on the side that corner
    # names, because the corner only says where to leave from.
    end = connection.target_anchor or _SIDE[across, up, out]
    step = ",".join(_format(way * connection.clearance) for way in (across, up, out))
    # Having stepped sideways, come back on the other axis first, so the arrow
    # meets the target square on rather than at a slant. An arrow that stepped
    # along the depth axis runs straight to the target instead: a square turn
    # is a turn on the page, and depth is drawn across the page as well as
    # down it.
    corner = "--" if out else "|-" if across else "-|"
    return (
        f"\\draw [{line}] ({connection.source}-{start.value}) -- ++({step})\n"
        f"    {corner}{head} ({connection.target}-{end.value});"
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
    edges = "\n".join(
        f"    \\draw [syEdge] ({source}-{start}) -- ({target}-{end});"
        for start in starts
        for end in ends
    )
    return f"\\begin{{pgfonlayer}}{{syBackground}}\n{edges}\n\\end{{pgfonlayer}}"


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


#: How far below the lowest point of a row its captions sit, in centimetres.
#: Enough to clear the size labels along the bottom edge of a box.
CAPTION_DROP = 0.4


def _baselines(diagram: Diagram, scale: float) -> tuple[dict[str, str], list[str]]:
    """Return the line each caption sits on, and the TikZ that defines them.

    Layers drawn at the same height share one line, so their captions read as a
    row. A drawing with a second row of layers below the first gets a second
    line, rather than dropping those captions onto the first and printing them
    over the ones already there.

    Returns
    -------
    tuple of (dict of str to str, list of str)
        The coordinate each captioned layer aligns to, keyed by layer name, and
        the statements to write before the layers. A row with nothing captioned
        appears in neither.
    """
    heights = diagram.axis_heights()
    rows: dict[float, list[Layer]] = {}
    for layer in diagram.layers:
        rows.setdefault(round(heights[layer.name], 6), []).append(layer)

    aligned: dict[str, str] = {}
    setup: list[str] = []
    for height, members in sorted(rows.items(), reverse=True):
        if not any(member.caption for member in members):
            continue
        name = f"syBaseline{len(setup) + 1}"
        floor = height - max(member.floor(scale) for member in members)
        setup.append(f"\\coordinate ({name}) at (0,{_format(floor - CAPTION_DROP)});")
        aligned.update(dict.fromkeys((member.name for member in members), name))
    return aligned, setup


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
    aligned, setup = _baselines(diagram, scale)
    blocks = list(setup)
    blocks += [
        layer.to_tikz(
            DrawContext(
                theme=diagram.theme,
                scale=scale,
                attach=attach,
                baseline=aligned.get(layer.name, ""),
            )
        )
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
