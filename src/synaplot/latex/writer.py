"""Turns a diagram into LaTeX source."""

from __future__ import annotations

from functools import lru_cache
from importlib.resources import files
from typing import TYPE_CHECKING

from synaplot.core.base import DrawContext, Layer, tikz_colour
from synaplot.core.diagram import FORWARD_FACES, Bend, ConnectionStyle, Flow
from synaplot.core.geometry import Anchor
from synaplot.core.theme import color_macro

if TYPE_CHECKING:
    from synaplot.core.diagram import Annotation, Connection, Diagram
    from synaplot.core.geometry import Offset

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
    syAnnotation/.style={ultra thick, draw=EDGE, opacity=0.7},
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
        # A forward arrow runs between the faces the flow points at, so a
        # diagram that stacks upward needs no anchors written on every arrow.
        flow = diagram.flow if diagram is not None else Flow.RIGHT
        leaves, arrives = FORWARD_FACES[flow]
        start = (connection.source_anchor or leaves).value
        end = (connection.target_anchor or arrives).value
        return f"\\draw [{line}] ({source}-{start}) --{head} ({target}-{end});"

    if connection.style is ConnectionStyle.BYPASS:
        return _bypass(connection, line, head, diagram)

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

#: How far a bypass steps out when nothing says and nothing can be worked out.
DEFAULT_CLEARANCE = 1.5

#: Which face a bypass comes back in on, per direction it stepped out in.
_SIDE = {
    (1, 0, 0): Anchor.EAST,
    (-1, 0, 0): Anchor.WEST,
    (0, 1, 0): Anchor.NORTH,
    (0, -1, 0): Anchor.SOUTH,
    (0, 0, 1): Anchor.NEAR,
    (0, 0, -1): Anchor.FAR,
}


def _bypass(
    connection: Connection, line: str, head: str, diagram: Diagram | None
) -> str:
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
    clearance = _clearance(connection, start, out, diagram)
    step = ",".join(_format(way * clearance) for way in (across, up, out))
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


def _clearance(
    connection: Connection, start: Anchor, out: int, diagram: Diagram | None
) -> float:
    """Return how far a bypass steps out before it runs past.

    An arrow stepping along the depth axis is heading for a lane, and where
    that lane is is where its target was placed, so the step is the depth
    between the two. Stepping any other distance leaves the last leg of the
    arrow slanting through the drawing, which is what makes several such arrows
    cross.
    """
    if connection.clearance is not None:
        return connection.clearance
    if not out or diagram is None:
        return DEFAULT_CLEARANCE
    depths = diagram.axes()
    scale = diagram.scale.value
    leaves = depths[connection.source][1] + start.dive * (
        diagram[connection.source].depth_extent(scale) / 2
    )
    return (depths[connection.target][1] - leaves) * out


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


def _caption_rows(diagram: Diagram) -> list[list[Layer]]:
    """Return the layers of each row that has a caption on it.

    Layers whose axes coincide are a row, and the captions of a row sit on one
    line so that they read as a line. A row with nothing captioned needs no
    line and is left out.

    Returns
    -------
    list of list of Layer
        The members of each captioned row, topmost row first. Every member is
        listed, captioned or not, because an uncaptioned layer can still be the
        one that reaches lowest and so decides where the line goes.
    """
    axes = diagram.axes()
    rows: dict[tuple[float, float], list[Layer]] = {}
    for layer in diagram.layers:
        height, depth = axes[layer.name]
        rows.setdefault((round(height, 6), round(depth, 6)), []).append(layer)
    return [
        members
        # A row set further towards the reader is drawn lower on the page, so
        # it comes after one at the same height but further away.
        for _, members in sorted(
            rows.items(), key=lambda row: (row[0][0], -row[0][1]), reverse=True
        )
        if any(member.caption for member in members)
    ]


def _captions(row: list[Layer], index: int) -> str:
    """Return the TikZ that writes one row's captions.

    Parameters
    ----------
    row
        The layers of the row, as :func:`_caption_rows` returns them.
    index
        Which captioned row this is, used to name its baseline.
    """
    base = f"syBaseline{index}"
    members = ",".join(layer.name for layer in row)
    return "\n".join(
        [f"\\syRowBase{{{base}}}{{{members}}}"]
        + [
            f"\\syCaption{{{layer.name}}}{{{base}}}{{{layer.caption}}}"
            for layer in row
            if layer.caption
        ]
    )


def annotation_to_tikz(annotation: Annotation) -> str:
    """Return the TikZ that draws one labelled arrow beside a layer.

    The arrow runs between a point on the layer and a point in the space around
    it, and the label sits at that far point on the side the arrow came from,
    so that it hugs the arrow rather than reaching further out than it.

    Parameters
    ----------
    annotation
        The arrow to draw.

    Returns
    -------
    str
        One TikZ statement.
    """
    near = _shifted(f"{annotation.layer}-{annotation.anchor.value}", annotation.offset)
    label = f"node[anchor={_label_anchor(annotation)}] {{{annotation.text}}}"
    # The arrowhead sits partway along the line, as it does on a connection,
    # and turns with it.
    head = "node[sloped,allow upside down] {\\syArrow}"
    reach = annotation.reach.to_tikz()
    if annotation.inward:
        return f"\\draw [syAnnotation] {near} ++{reach} {label} -- {head} {near};"
    return f"\\draw [syAnnotation] {near} -- {head} ++{reach} {label};"


def _shifted(coordinate: str, offset: Offset) -> str:
    """Return a TikZ coordinate, shifted when the offset asks for it."""
    if offset == type(offset)():
        return f"({coordinate})"
    return f"([shift={{{offset.to_tikz()}}}] {coordinate})"


def _label_anchor(annotation: Annotation) -> str:
    """Return which corner of an annotation's label sits at the end of its arrow.

    The label is pinned on the side the arrow came from, so it lies along the
    arrow. Two arrows into the same face, one offset up and one down, then get
    their labels above and below rather than on top of each other.
    """
    up = _sign(annotation.offset.y) or -_sign(annotation.reach.y)
    across = _sign(annotation.reach.x)
    corner = [
        {1: "south", -1: "north"}.get(up, ""),
        {1: "east", -1: "west"}.get(across, ""),
    ]
    return " ".join(part for part in corner if part) or "center"


def _sign(value: float | str) -> int:
    """Return which way a distance goes, or 0 for one only the drawing knows."""
    if isinstance(value, str):
        return 0
    return (value > 0) - (value < 0)


def legend_to_tikz(diagram: Diagram) -> str:
    """Return the TikZ that draws a diagram's legend.

    Parameters
    ----------
    diagram
        The diagram to draw the legend of.

    Returns
    -------
    str
        One TikZ statement, or an empty string when the diagram has no legend
        or nothing to put in one.
    """
    entries = diagram.legend_entries()
    if diagram.legend is None or not entries:
        return ""
    rows = "\n".join(
        f"    \\syLegendItem{{{tikz_colour(entry.fill, entry.role)}}}"
        f"{{{entry.opacity}}}{{{entry.label}}}"
        for entry in entries
    )
    corner = diagram.legend.position
    pinned, step = corner.outside
    return f"\\syLegend{{{corner.value}}}{{{pinned}}}{{{step}}}{{%\n{rows}}}"


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
    rows = _caption_rows(diagram)
    # A captioned row hangs its captions from the lowest point any of its layers
    # reached, so those layers are drawn inside a scope that records it.
    measured = {layer.name for row in rows for layer in row}
    blocks = []
    for layer, attach in diagram.placements():
        drawing = layer.to_tikz(
            DrawContext(theme=diagram.theme, scale=scale, attach=attach)
        )
        if layer.name in measured:
            drawing = (
                f"\\begin{{scope}}[local bounding box=syExtent-{layer.name}]\n"
                f"{drawing}\n\\end{{scope}}"
            )
        blocks.append(drawing)
    roof = max((layer.half_height(scale) for layer in diagram.layers), default=0.0)
    blocks += [connection_to_tikz(c, roof, diagram) for c in diagram.connections]
    blocks += [annotation_to_tikz(a) for a in diagram.annotations]
    blocks += [_captions(row, index) for index, row in enumerate(rows, start=1)]
    # The legend is drawn last, so that it can be placed against the edge of
    # everything else the diagram drew.
    blocks += [block for block in [legend_to_tikz(diagram)] if block]
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
