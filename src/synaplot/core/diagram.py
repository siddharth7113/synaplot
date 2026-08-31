"""A diagram: the layers it draws and the arrows between them."""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field, SerializeAsAny, field_validator

from synaplot.core.base import Layer
from synaplot.core.geometry import Anchor, Attach, Offset, Scale
from synaplot.core.theme import Theme

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path


DEPTH_SLANT = 0.385
"""How far across the page TikZ draws one unit of depth.

TikZ projects the depth axis onto ``(-0.385, -0.385)`` by default, so a layer
takes up horizontal room in proportion to how deep it is drawn.
"""


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
    """

    FORWARD = "forward"
    SKIP = "skip"
    ELBOW = "elbow"


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
        How far above the layers a skip arrow runs, as a fraction of the layer
        height. Only a skip arrow uses it.
    bend
        Which way an elbow arrow turns. Only an elbow arrow uses it.

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
        Multiplier applied to every size in the diagram.
    gap
        Horizontal space left between two layers that are chained together.
        ``None`` works it out from how deep the two layers are drawn, which is
        usually what you want. Set a number to space every pair equally.
    layers
        The layers to draw, in drawing order.
    margin
        Space left between two layers on top of the room their depth takes up.
        Ignored when ``gap`` is set.
    connections
        Arrows between layers.

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

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str = "diagram"
    theme: Theme = Field(default_factory=Theme)
    scale: Scale = Field(default_factory=Scale)
    gap: float | None = None
    margin: float = 1.0
    # SerializeAsAny keeps each layer's own fields. Without it pydantic
    # writes only what the Layer base declares, dropping filters, sizes,
    # and everything else a specific layer adds.
    layers: list[SerializeAsAny[Layer]] = Field(default_factory=list)
    connections: list[Connection] = Field(default_factory=list)

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

    def placements(self) -> Iterator[tuple[Layer, Attach | None]]:
        """Work out where each layer goes.

        A layer that names its own position keeps it. A layer that does not is
        placed to the right of the previous layer, separated by
        :attr:`Diagram.gap`. The first such layer sits at the origin.

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
                attach = Attach(
                    layer=previous.name,
                    anchor=Anchor.EAST,
                    offset=Offset(x=self._gap_between(previous, layer)),
                )
            yield layer, attach
            previous = layer

    def _gap_between(self, before: Layer, after: Layer) -> float:
        """Return how far apart to place two layers that follow one another.

        TikZ draws the depth axis diagonally, at :data:`DEPTH_SLANT` of a unit
        across for every unit deep. A layer therefore reaches further to each
        side than its width alone, and two deep layers placed a fixed distance
        apart overlap on the page. The space needed is half the projected depth
        of each, plus a margin so the arrow between them is visible.
        """
        if self.gap is not None:
            return self.gap
        scale = self.scale.value
        reach = (
            DEPTH_SLANT * (before.depth_extent(scale) + after.depth_extent(scale)) / 2
        )
        return reach + self.margin

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

    def save(self, path: str | Path, *, dpi: int = 300) -> Path:
        """Write this diagram to a file.

        The format comes from the file's suffix: ``.tex``, ``.pdf``, ``.svg``,
        or ``.png``.

        Parameters
        ----------
        path
            Where to write the diagram.
        dpi
            Resolution for PNG output.

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

        return render(self, path, dpi=dpi)
