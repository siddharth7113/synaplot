"""Where a layer sits in a diagram and how big it is drawn."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Anchor(str, Enum):
    """A named point on a drawn layer that other layers can attach to.

    The members are the coordinates the ``Box`` pic defines, which a test holds
    them to. A ball defines only the five returned by :meth:`ball_anchors`, so
    attaching to the corner of a ball fails when the diagram is checked.

    A name reads outwards from the depth axis: ``nearsoutheast`` is the corner
    towards the reader, at the bottom, on the right.

    Examples
    --------
    >>> Anchor.EAST.value
    'east'
    >>> Anchor.NORTHEAST in Anchor.ball_anchors()
    False
    """

    ANCHOR = "anchor"
    EAST = "east"
    WEST = "west"
    NORTH = "north"
    SOUTH = "south"
    NEAR = "near"
    FAR = "far"
    NEARWEST = "nearwest"
    NEAREAST = "neareast"
    FARWEST = "farwest"
    FAREAST = "fareast"
    NORTHEAST = "northeast"
    NORTHWEST = "northwest"
    SOUTHEAST = "southeast"
    SOUTHWEST = "southwest"
    NEARNORTHEAST = "nearnortheast"
    FARNORTHEAST = "farnortheast"
    NEARSOUTHEAST = "nearsoutheast"
    FARSOUTHEAST = "farsoutheast"
    NEARNORTHWEST = "nearnorthwest"
    FARNORTHWEST = "farnorthwest"
    NEARSOUTHWEST = "nearsouthwest"
    FARSOUTHWEST = "farsouthwest"

    @property
    def rise(self) -> int:
        """Return whether this anchor is on the top face, the bottom, or neither.

        Returns
        -------
        int
            1 on the top face, -1 on the bottom, 0 in between. Multiply by half
            a layer's height to get how far the anchor sits from its axis.

        Examples
        --------
        >>> Anchor.NORTHEAST.rise, Anchor.SOUTH.rise, Anchor.NEAR.rise
        (1, -1, 0)
        """
        if "north" in self.value:
            return 1
        return -1 if "south" in self.value else 0

    @property
    def dive(self) -> int:
        """Return whether this anchor is on the near face, the far one, or neither.

        Returns
        -------
        int
            1 on the face towards the reader, -1 on the face away from them, 0
            in between. Multiply by half a layer's depth to get how far the
            anchor sits from its axis.

        Examples
        --------
        >>> Anchor.NEARSOUTHWEST.dive, Anchor.FAREAST.dive, Anchor.NORTH.dive
        (1, -1, 0)
        """
        if "near" in self.value:
            return 1
        return -1 if "far" in self.value else 0

    @classmethod
    def ball_anchors(cls) -> frozenset[Anchor]:
        """Return the anchors that a ball defines.

        Returns
        -------
        frozenset of Anchor
            The five anchors available on a ball.

        Examples
        --------
        >>> sorted(a.value for a in Anchor.ball_anchors())
        ['anchor', 'east', 'north', 'south', 'west']
        """
        return frozenset({cls.ANCHOR, cls.EAST, cls.WEST, cls.NORTH, cls.SOUTH})


class Offset(BaseModel):
    r"""A shift applied on top of an anchor, in TikZ units.

    Parameters
    ----------
    x, y, z
        Distance to shift along each axis. Default is no shift. A string is
        passed to TikZ as an expression, which is how a distance that only the
        drawing knows, such as how far across the page a unit of depth goes,
        gets into an offset.

    Examples
    --------
    >>> Offset(x=2).to_tikz()
    '(2,0,0)'
    >>> Offset(x=1.5, y=-2).to_tikz()
    '(1.5,-2,0)'

    An expression is braced, so that TikZ reads it as one component rather than
    as the start of another coordinate:

    >>> Offset(x=r"2*\syDepthSlant").to_tikz()
    '({2*\\syDepthSlant},0,0)'
    """

    model_config = ConfigDict(frozen=True)

    x: float | str = 0.0
    y: float | str = 0.0
    z: float | str = 0.0

    def to_tikz(self) -> str:
        """Return the offset as a TikZ coordinate.

        Returns
        -------
        str
            A three-dimensional TikZ coordinate such as ``'(2,0,0)'``.
        """
        return "(" + ",".join(_component(v) for v in (self.x, self.y, self.z)) + ")"


def _component(value: float | str) -> str:
    """Return one component of an offset, ready to put in a coordinate."""
    return "{" + value + "}" if isinstance(value, str) else _number(value)


class Attach(BaseModel):
    """Place a layer relative to another layer.

    Parameters
    ----------
    layer
        Name of the layer to attach to.
    anchor
        Which point on that layer to attach to. Default is its east face, which
        places this layer to the right of it.
    offset
        Shift applied after the anchor, in TikZ units. Use it to leave a gap.

    Examples
    --------
    >>> Attach(layer="conv1").to_tikz()
    '(conv1-east)'
    >>> Attach(layer="conv1", anchor=Anchor.NORTH).to_tikz()
    '(conv1-north)'
    """

    model_config = ConfigDict(frozen=True)

    layer: str
    anchor: Anchor = Anchor.EAST
    offset: Offset = Offset()

    def to_tikz(self) -> str:
        """Return the TikZ coordinate this attachment names.

        Returns
        -------
        str
            A TikZ coordinate such as ``'(conv1-east)'``.
        """
        return f"({self.layer}-{self.anchor.value})"


class Size(BaseModel):
    """The drawn size of a layer, in TikZ units before scaling.

    These are drawing sizes, not tensor shapes. They control how large the box
    looks, and are usually chosen so that a shrinking feature map is drawn as a
    shrinking box.

    Parameters
    ----------
    width
        Thickness of the box. A list draws that many boxes side by side, which
        is how a run of repeated convolutions is drawn as one layer.
    height
        Height of the box.
    depth
        Depth of the box.

    Examples
    --------
    >>> Size(width=2).width_to_tikz()
    '2'
    >>> Size(width=[2, 2, 2]).width_to_tikz()
    '{2,2,2}'
    >>> Size(width=[2, 2, 2]).boxes
    3
    """

    model_config = ConfigDict(frozen=True)

    width: float | list[float] = 1.0
    height: float = 40.0
    depth: float = 40.0

    @field_validator("width")
    @classmethod
    def _reject_empty_width(cls, value: float | list[float]) -> float | list[float]:
        if isinstance(value, list) and not value:
            raise ValueError("width must be a number or a non-empty list of numbers")
        return value

    @property
    def boxes(self) -> int:
        """Return how many boxes this size draws."""
        return len(self.width) if isinstance(self.width, list) else 1

    def width_to_tikz(self) -> str:
        """Return the width in the form a box pic expects.

        Returns
        -------
        str
            A single number, or a braced comma-separated list when the width
            describes several boxes.
        """
        if isinstance(self.width, list):
            return "{" + ",".join(_number(w) for w in self.width) + "}"
        return _number(self.width)


class Scale(BaseModel):
    """How TikZ units map to the size of the drawing.

    Parameters
    ----------
    value
        Multiplier applied to every size in the diagram. Must be positive.

    Examples
    --------
    >>> Scale().value
    0.2
    """

    model_config = ConfigDict(frozen=True)

    value: float = Field(default=0.2, gt=0)


def _number(value: float) -> str:
    """Format a number for LaTeX, dropping a trailing ``.0``.

    Parameters
    ----------
    value
        The number to format.

    Returns
    -------
    str
        The number without a redundant decimal part.

    Examples
    --------
    >>> _number(2.0)
    '2'
    >>> _number(1.5)
    '1.5'
    >>> _number(-0.25)
    '-0.25'
    """
    if value == int(value):
        return str(int(value))
    return repr(round(value, 6))
