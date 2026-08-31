"""A diagram: the layers it draws and the arrows between them."""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field, SerializeAsAny, field_validator

from synaplot.core.base import Layer
from synaplot.core.geometry import Anchor, Attach, Offset
from synaplot.core.theme import Theme

if TYPE_CHECKING:
    from collections.abc import Iterator

    from synaplot.render import Renderer

from pathlib import Path


class ConnectionStyle(str, Enum):
    """How a connection is drawn.

    Attributes
    ----------
    FORWARD
        A straight arrow from one layer to the next.
    SKIP
        An arrow that leaves the top of the source, runs above the diagram, and
        comes down onto the target. Used where a straight arrow would cut
        through the layers in between.
    ELBOW
        An arrow that turns one right angle on its way. Use it for a branch
        that leaves the main line, since a straight arrow between two layers
        that are neither level nor stacked reads as a long diagonal across the
        drawing.
    BYPASS
        An arrow that steps out to one side, runs past whatever is in the way,
        and comes back in. This is the shape of a residual connection around a
        sublayer. An elbow cannot draw one, because going around something
        takes two turns and an elbow makes one.
    FULL
        A thin line from every node of one layer to every node of the next,
        with no arrowhead. This is how a fully connected layer is drawn. Both
        layers must be drawn as nodes; see
        :meth:`~synaplot.core.base.Layer.node_names`.
    """

    FORWARD = "forward"
    SKIP = "skip"
    ELBOW = "elbow"
    BYPASS = "bypass"
    FULL = "full"


class Flow(str, Enum):
    """Which way a chain of layers runs.

    Attributes
    ----------
    RIGHT
        Each layer goes to the right of the one before it, which is how a stack
        of feature maps is drawn.
    UP
        Each layer goes above the one before it, which is how the blocks of a
        transformer or a recurrent cell are drawn.
    """

    RIGHT = "right"
    UP = "up"


#: Which faces a forward arrow runs between, per flow direction.
FORWARD_FACES = {
    Flow.RIGHT: (Anchor.EAST, Anchor.WEST),
    Flow.UP: (Anchor.NORTH, Anchor.SOUTH),
}


class Bend(str, Enum):
    """Which way an elbow turns.

    Attributes
    ----------
    ACROSS_THEN_DOWN
        Travel horizontally out of the source, then vertically into the target.
    DOWN_THEN_ACROSS
        Travel vertically out of the source, then horizontally into the target.
    """

    ACROSS_THEN_DOWN = "across_then_down"
    DOWN_THEN_ACROSS = "down_then_across"


class Connection(BaseModel):
    """An arrow from one layer to another.

    Parameters
    ----------
    source, target
        Names of the layers the arrow runs between.
    style
        How to draw the arrow.
    source_anchor, target_anchor
        Which point on each layer to attach the arrow to. ``None`` lets the
        style choose: a forward arrow runs east to west.
    height
        How far above the layers a skip arrow runs, as a multiple of the
        tallest layer's half height. Only a skip arrow uses it.
    bend
        Which way an elbow arrow turns. Only an elbow arrow uses it.
    clearance
        How far a bypass arrow steps out before running past. ``None`` works it
        out: an arrow stepping along the depth axis steps exactly into the lane
        its target sits in, so that the run to the target is level. Only a
        bypass arrow uses it.

    Examples
    --------
    >>> Connection(source="conv1", target="pool1").style.value
    'forward'
    """

    model_config = ConfigDict(frozen=True)

    source: str
    target: str
    style: ConnectionStyle = ConnectionStyle.FORWARD
    source_anchor: Anchor | None = None
    target_anchor: Anchor | None = None
    height: float = 1.25
    bend: Bend = Bend.ACROSS_THEN_DOWN
    clearance: float | None = None


class Annotation(BaseModel):
    r"""A labelled arrow drawn beside one layer.

    A connection runs between two layers. An annotation runs between a layer
    and a point in the space around it, which is how a drawing names what goes
    into a layer or comes out of it without drawing the layer that supplies it.

    Parameters
    ----------
    layer
        Name of the layer the arrow touches.
    text
        The label. Read as LaTeX, so ``$\frac{\partial L}{\partial p}$``
        renders as math.
    anchor
        Which point on the layer the arrow touches.
    offset
        Shift applied to that anchor, in TikZ units. Use it to run two arrows
        into the same face, one above the other.
    reach
        How far the far end of the arrow sits from the near end, in TikZ units.
        The label goes at the far end, on the side the arrow came from.
    inward
        Whether the arrow points at the layer or away from it.

    Examples
    --------
    >>> Annotation(layer="loss", text="$p$", reach=Offset(x=-4)).inward
    True
    """

    model_config = ConfigDict(frozen=True)

    layer: str
    text: str
    anchor: Anchor = Anchor.WEST
    offset: Offset = Offset()
    reach: Offset = Offset()
    inward: bool = True


class LegendEntry(BaseModel):
    """One row of a legend: a color and what it stands for.

    Parameters
    ----------
    label
        What the color stands for. Read as LaTeX.
    role
        Which color of the theme to draw, named by the field on
        :class:`~synaplot.core.theme.Theme` that holds it, such as ``'pool'``.
    fill
        Color to draw instead, overriding the theme.
    opacity
        How opaque the swatch is, so that it matches the layers it describes.
    """

    model_config = ConfigDict(frozen=True)

    label: str
    role: str = "conv"
    fill: str | None = None
    opacity: float = Field(default=0.7, ge=0, le=1)


class Corner(str, Enum):
    """Which corner of a drawing something sits in.

    The members are TikZ node anchors, so they name the corner of the legend
    that is pinned as well as the corner of the drawing it is pinned to.
    """

    NORTH_EAST = "north east"
    NORTH_WEST = "north west"
    SOUTH_EAST = "south east"
    SOUTH_WEST = "south west"

    @property
    def outside(self) -> tuple[str, int]:
        """Return where a key pinned to this corner goes.

        A key sits just clear of the drawing rather than over it, so that a
        corner holding part of the diagram is not covered. Pinning the
        opposite corner of the key, above or below, is what puts it there.

        Returns
        -------
        tuple of (str, int)
            The corner of the key to pin, and which way it clears the drawing:
            -1 for below, 1 for above.

        Examples
        --------
        >>> Corner.SOUTH_EAST.outside
        ('north east', -1)
        """
        if "south" in self.value:
            return self.value.replace("south", "north"), -1
        return self.value.replace("north", "south"), 1


class Legend(BaseModel):
    """A key drawn in a corner of the diagram.

    Parameters
    ----------
    position
        Which corner to draw it in.
    entries
        The rows to draw. Leave it empty to get one row for each kind of layer
        the diagram draws, in drawing order, named and colored as that layer
        is.
    """

    position: Corner = Corner.SOUTH_EAST
    entries: list[LegendEntry] = Field(default_factory=list)


def _distance(name: str, offset: float | str, axis: str) -> float:
    """Return an offset as a number, or say why it is not one.

    Raises
    ------
    ValueError
        If the offset is a TikZ expression, whose value only the drawing knows.
    """
    if isinstance(offset, int | float):
        return float(offset)
    raise ValueError(
        f"{name!r} is offset along {axis} by a TikZ expression, so where it sits "
        f"is not known here; give that offset as a number"
    )


class Diagram(BaseModel):
    """A network drawing, built from layers and the arrows between them.

    Layers are drawn in the order they are added. A layer that does not say
    where it goes is placed to the right of the one before it, so a plain
    feed-forward network needs no positioning at all.

    Parameters
    ----------
    name
        Identifies the diagram. Used as the default output file name.
    theme
        Colors for the diagram.
    scale
        Multiplier applied to every size in the diagram. Must be positive.
    flow
        Which way a chain of layers runs. Layers that do not say where they go
        follow this direction, and a forward arrow runs between the faces it
        points at, so a plain stack needs no positioning and no anchors.
    gap
        Space left between two layers that are chained together. ``None`` works
        it out, which for a row of feature maps means allowing for how deep
        each is drawn. Set a number to space every pair equally.
    layers
        The layers to draw, in drawing order.
    margin
        Space left between two layers on top of the room their depth takes up.
        Ignored when ``gap`` is set.
    connections
        Arrows between layers.
    annotations
        Labelled arrows drawn beside a layer.
    legend
        A key naming the kinds of layer the diagram draws. ``None`` draws none.

    Examples
    --------
    ``add`` and ``connect`` return the diagram, so they chain:

    >>> from synaplot.layers import Conv, Pool
    >>> diagram = (
    ...     Diagram(name="tiny")
    ...     .add(Conv(name="conv1", filters=64, spatial=224))
    ...     .add(Pool(name="pool1"))
    ...     .connect("conv1", "pool1")
    ... )
    >>> [layer.name for layer in diagram.layers]
    ['conv1', 'pool1']

    Names must be unique, because a connection refers to a layer by name:

    >>> diagram.add(Pool(name="pool1"))
    Traceback (most recent call last):
        ...
    ValueError: a layer named 'pool1' is already in this diagram
    """

    name: str = "diagram"
    theme: Theme = Field(default_factory=Theme)
    scale: float = Field(default=0.2, gt=0)
    flow: Flow = Flow.RIGHT
    gap: float | None = None
    margin: float = 1.0
    # SerializeAsAny keeps each layer's own fields. Without it pydantic
    # writes only what the Layer base declares, dropping filters, sizes,
    # and everything else a specific layer adds.
    layers: list[SerializeAsAny[Layer]] = Field(default_factory=list)
    connections: list[Connection] = Field(default_factory=list)
    annotations: list[Annotation] = Field(default_factory=list)
    legend: Legend | None = None

    @field_validator("layers")
    @classmethod
    def _reject_duplicate_names(cls, layers: list[Layer]) -> list[Layer]:
        seen: set[str] = set()
        for layer in layers:
            if layer.name in seen:
                raise ValueError(f"a layer named {layer.name!r} appears twice")
            seen.add(layer.name)
        return layers

    def add(self, *layers: Layer) -> Diagram:
        """Add layers to the diagram.

        Parameters
        ----------
        *layers
            The layers to add, in drawing order.

        Returns
        -------
        Diagram
            This diagram, so calls can be chained.

        Raises
        ------
        ValueError
            If a layer's name is already used in this diagram.
        """
        for layer in layers:
            if any(existing.name == layer.name for existing in self.layers):
                raise ValueError(
                    f"a layer named {layer.name!r} is already in this diagram"
                )
            self.layers.append(layer)
        return self

    def connect(
        self,
        source: str,
        target: str,
        style: ConnectionStyle | str = ConnectionStyle.FORWARD,
        **kwargs: object,
    ) -> Diagram:
        """Draw an arrow between two layers.

        Parameters
        ----------
        source, target
            Names of the layers to connect. Both must already be in the
            diagram.
        style
            How to draw the arrow.
        **kwargs
            Further fields for :class:`Connection`, such as ``height``.

        Returns
        -------
        Diagram
            This diagram, so calls can be chained.

        Raises
        ------
        KeyError
            If either name is not a layer in this diagram.
        """
        for name in (source, target):
            if name not in self:
                raise KeyError(f"no layer named {name!r} in this diagram")
        self.connections.append(
            Connection(source=source, target=target, style=style, **kwargs)
        )
        return self

    def annotate(self, layer: str, text: str, **kwargs: object) -> Diagram:
        r"""Draw a labelled arrow beside a layer.

        Parameters
        ----------
        layer
            Name of the layer to annotate. It must already be in the diagram.
        text
            The label, read as LaTeX.
        **kwargs
            Further fields for :class:`Annotation`, such as ``reach``.

        Returns
        -------
        Diagram
            This diagram, so calls can be chained.

        Raises
        ------
        KeyError
            If the name is not a layer in this diagram.
        """
        if layer not in self:
            raise KeyError(f"no layer named {layer!r} in this diagram")
        self.annotations.append(Annotation(layer=layer, text=text, **kwargs))
        return self

    def add_legend(self, **kwargs: object) -> Diagram:
        """Draw a key naming the kinds of layer in the diagram.

        Parameters
        ----------
        **kwargs
            Fields for :class:`Legend`, such as ``position``. With none, the
            key lists every kind of layer the diagram draws, in a corner.

        Returns
        -------
        Diagram
            This diagram, so calls can be chained.
        """
        self.legend = Legend(**kwargs)
        return self

    def legend_entries(self) -> list[LegendEntry]:
        """Return the rows the legend draws.

        A legend that lists its own rows keeps them. One that does not gets a
        row for each kind of layer the diagram draws, in drawing order. A layer
        that names no kind of thing, such as an input image or a block that
        carries its own text, is left out.

        Returns
        -------
        list of LegendEntry
            The rows, or an empty list when the diagram has no legend.
        """
        if self.legend is None:
            return []
        if self.legend.entries:
            return self.legend.entries
        rows: dict[str, LegendEntry] = {}
        for layer in self.layers:
            if layer.title:
                rows.setdefault(
                    layer.title,
                    LegendEntry(
                        label=layer.title,
                        role=layer.role,
                        fill=layer.fill,
                        opacity=layer.legend_opacity,
                    ),
                )
        return list(rows.values())

    def __contains__(self, name: object) -> bool:
        """Return whether a layer of that name is in the diagram."""
        return any(layer.name == name for layer in self.layers)

    def __getitem__(self, name: str) -> Layer:
        """Return the layer with that name.

        Raises
        ------
        KeyError
            If no layer has that name.
        """
        for layer in self.layers:
            if layer.name == name:
                return layer
        raise KeyError(f"no layer named {name!r} in this diagram")

    def assets(self) -> list[Path]:
        """Return every file the drawing reads, such as an input image.

        Returns
        -------
        list of pathlib.Path
            The files, in drawing order, without repeats.
        """
        found: dict[str, Path] = {}
        for layer in self.layers:
            for asset in layer.assets():
                found.setdefault(str(asset), asset)
        return list(found.values())

    def placements(self) -> Iterator[tuple[Layer, Attach | None]]:
        """Work out where each layer goes.

        A layer that names its own position keeps it. A layer that does not
        follows ``flow`` from the previous layer, separated by ``gap``. The
        first such layer sits at the origin.

        Yields
        ------
        tuple of (Layer, Attach or None)
            Each layer and the position it is drawn at. ``None`` means the
            origin.
        """
        previous: Layer | None = None
        for layer in self.layers:
            if layer.to is not None:
                attach = layer.to
            elif previous is None:
                attach = None
            else:
                attach = self._step(previous, layer)
            yield layer, attach
            previous = layer

    def axes(self) -> dict[str, tuple[float, float]]:
        """Return the height and the depth each layer's axis sits at.

        A layer sits centered on its own axis. Chaining leaves that axis where
        it was, and attaching to a face of another layer moves it by half that
        layer's height or depth. Layers whose axes coincide form a row, which
        is what the writer needs to know to give each row of a drawing its own
        line of captions. Depth counts as well as height, because TikZ draws
        the depth axis diagonally, so a layer set towards the reader is drawn
        lower on the page than the row it was chained from.

        Returns
        -------
        dict of str to tuple of (float, float)
            Each layer name, and how far its axis sits above and in front of
            the first layer's, in TikZ units.

        Raises
        ------
        ValueError
            If a layer is attached to one that has not been placed yet, or is
            offset by a TikZ expression rather than a number.

        Examples
        --------
        >>> from synaplot.layers import Conv, Pool
        >>> from synaplot.core.geometry import Anchor, Attach
        >>> diagram = Diagram(name="two").add(
        ...     Conv(name="conv1"),
        ...     Pool(name="below", to=Attach(layer="conv1", anchor=Anchor.SOUTH)),
        ... )
        >>> diagram.axes()
        {'conv1': (0.0, 0.0), 'below': (-4.0, 0.0)}
        """
        scale = self.scale
        axes: dict[str, tuple[float, float]] = {}
        for layer, attach in self.placements():
            if attach is None:
                axes[layer.name] = (0.0, 0.0)
                continue
            if attach.layer not in axes:
                raise ValueError(
                    f"{layer.name!r} is attached to {attach.layer!r}, which comes "
                    f"later in the diagram; attach it to a layer already added"
                )
            face = self[attach.layer]
            height, depth = axes[attach.layer]
            axes[layer.name] = (
                height
                + attach.anchor.rise * face.half_height(scale)
                + _distance(layer.name, attach.offset.y, "y"),
                depth
                + attach.anchor.dive * face.depth_extent(scale) / 2
                + _distance(layer.name, attach.offset.z, "z"),
            )
        return axes

    def _step(self, before: Layer, after: Layer) -> Attach:
        r"""Return where a layer goes when it follows another along the flow.

        Going right, a layer's west face lands on the previous layer's east, so
        the offset is the space between them. TikZ draws the depth axis
        diagonally, so two layers drawn as volumes reach towards each other and
        need room for both depths on top of the margin. How far a unit of depth
        reaches is left to ``\\syDepthSlant``, which reads it off the picture's
        own z axis: writing the number here would be a guess about a setting
        the drawing is free to change.

        Going up, a layer's own middle lands on the previous layer's top, so
        half its height is added to the space.
        """
        scale = self.scale
        if self.flow is Flow.UP:
            space = self.margin if self.gap is None else self.gap
            return Attach(
                layer=before.name,
                anchor=Anchor.NORTH,
                offset=Offset(y=space + after.half_height(scale)),
            )
        if self.gap is not None:
            step: float | str = self.gap
        else:
            depth = before.depth_extent(scale) + after.depth_extent(scale)
            step = f"{depth / 2:g}*\\syDepthSlant+{self.margin:g}"
        return Attach(layer=before.name, anchor=Anchor.EAST, offset=Offset(x=step))

    def to_tikz(self) -> str:
        """Return the TikZ that draws this diagram, without a document around it.

        Returns
        -------
        str
            The body of a ``tikzpicture``.
        """
        from synaplot.latex.writer import diagram_to_tikz

        return diagram_to_tikz(self)

    def to_tex(self, *, standalone: bool = True) -> str:
        """Return a LaTeX document that draws this diagram.

        Parameters
        ----------
        standalone
            Whether to wrap the drawing in a document that compiles on its own.
            Pass ``False`` for a fragment to paste into a paper, which brings
            its own preamble.

        Returns
        -------
        str
            LaTeX source.
        """
        from synaplot.latex.writer import diagram_to_tex

        return diagram_to_tex(self, standalone=standalone)

    def save(
        self,
        path: str | Path,
        *,
        fmt: str | None = None,
        dpi: int = 300,
        renderer: type[Renderer] | None = None,
    ) -> Path:
        """Write this diagram to a file.

        Parameters
        ----------
        path
            Where to write the diagram.
        fmt
            Format to write: ``'tex'``, ``'pdf'``, ``'svg'``, or ``'png'``.
            ``None`` reads it from the suffix of ``path``.
        dpi
            Resolution for PNG output.
        renderer
            Compile with this renderer rather than the most preferred installed
            one.

        Returns
        -------
        Path
            The file that was written.

        Raises
        ------
        ToolchainError
            If no installed program can produce that format. The message names
            what to install.
        """
        from synaplot.render import render

        return render(self, path, fmt=fmt, dpi=dpi, renderer=renderer)
