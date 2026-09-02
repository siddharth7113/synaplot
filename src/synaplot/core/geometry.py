"""Where a layer sits in a diagram and how big it is drawn."""

from __future__ import annotations

import re
from enum import Enum

from pydantic import BaseModel, ConfigDict, field_validator


class Anchor(str, Enum):
    """A named point on a drawn layer that other layers can attach to.

    The members are the coordinates the ``Box`` pic defines, which a test holds
    them to. A layer drawn as something other than a box defines fewer: a ball
    defines the five returned by :meth:`ball_anchors`, a flat shape the nine
    returned by :meth:`flat_anchors`, and an image plane the seven returned by
    :meth:`plane_anchors`. Attaching to an anchor a layer does not define is
    refused when the diagram is drawn, rather than left to fail inside LaTeX.

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

    @property
    def run(self) -> int:
        """Return whether this anchor is on the east face, the west, or neither.

        Returns
        -------
        int
            1 on the east face, -1 on the west, 0 in between. With :attr:`rise`
            and :attr:`dive` this places an anchor on all three axes.

        Examples
        --------
        >>> Anchor.NORTHEAST.run, Anchor.FARWEST.run, Anchor.NORTH.run
        (1, -1, 0)
        """
        if "east" in self.value:
            return 1
        return -1 if "west" in self.value else 0

    @property
    def side(self) -> Anchor | None:
        """Return the face an arrow leaving this anchor steps out through.

        A face is its own side. A corner or an edge steps out through the side
        it names, east or west before north or south before near or far, so
        that an arrow leaving a corner runs parallel to one leaving the face
        beside it rather than back down the line the other came in on. The
        centre of a layer faces no way at all.

        Returns
        -------
        Anchor or None
            One of the six faces, or ``None`` for the centre.

        Examples
        --------
        >>> Anchor.NORTHEAST.side, Anchor.NEAR.side, Anchor.ANCHOR.side
        (<Anchor.EAST: 'east'>, <Anchor.NEAR: 'near'>, None)
        """
        for sign, faces in (
            (self.run, (Anchor.EAST, Anchor.WEST)),
            (self.rise, (Anchor.NORTH, Anchor.SOUTH)),
            (self.dive, (Anchor.NEAR, Anchor.FAR)),
        ):
            if sign:
                return faces[0] if sign > 0 else faces[1]
        return None

    @property
    def opposite(self) -> Anchor:
        """Return the anchor facing this one across the layer.

        Examples
        --------
        >>> Anchor.NORTHEAST.opposite
        <Anchor.SOUTHWEST: 'southwest'>
        >>> Anchor.NEAR.opposite, Anchor.ANCHOR.opposite
        (<Anchor.FAR: 'far'>, <Anchor.ANCHOR: 'anchor'>)
        """
        flipped = {
            "north": "south",
            "south": "north",
            "east": "west",
            "west": "east",
            "near": "far",
            "far": "near",
        }
        pattern = "|".join(flipped)
        return Anchor(re.sub(pattern, lambda found: flipped[found.group()], self.value))

    @property
    def tikz(self) -> str:
        """Return this anchor as TikZ names it on a node drawn flat on the page.

        TikZ writes a corner as two words. Only an anchor on the page has a
        TikZ name; ``near`` and ``far`` are synaplot's own.

        Examples
        --------
        >>> Anchor.NORTHEAST.tikz, Anchor.WEST.tikz, Anchor.ANCHOR.tikz
        ('north east', 'west', 'center')
        """
        if self is Anchor.ANCHOR:
            return "center"
        name: str = self.value
        return name.replace("north", "north ").replace("south", "south ").strip()

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

    @classmethod
    def flat_anchors(cls) -> frozenset[Anchor]:
        """Return the anchors a shape drawn flat on the page defines.

        Returns
        -------
        frozenset of Anchor
            The nine anchors available on a flat shape: the four sides, the
            four corners, and the centre. A flat shape has no depth, so it
            defines nothing along that axis.

        Examples
        --------
        >>> len(Anchor.flat_anchors())
        9
        >>> Anchor.NEAR in Anchor.flat_anchors()
        False
        """
        return cls.ball_anchors() | {
            cls.NORTHEAST,
            cls.NORTHWEST,
            cls.SOUTHEAST,
            cls.SOUTHWEST,
        }

    @classmethod
    def plane_anchors(cls) -> frozenset[Anchor]:
        """Return the anchors an image plane defines.

        Returns
        -------
        frozenset of Anchor
            The seven anchors available on a plane standing across the depth
            axis: its centre, its top and bottom, its near and far edges, and
            east and west, which both sit on the plane because it has no
            thickness to separate them.

        Examples
        --------
        >>> sorted(a.value for a in Anchor.plane_anchors())
        ['anchor', 'east', 'far', 'near', 'north', 'south', 'west']
        """
        return cls.ball_anchors() | {cls.NEAR, cls.FAR}


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
    return "{" + value + "}" if isinstance(value, str) else number(value)


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
            return "{" + ",".join(number(w) for w in self.width) + "}"
        return number(self.width)


def number(value: float) -> str:
    """Format a number for LaTeX, dropping a trailing ``.0``.

    A drawing is full of numbers, and ``40.0`` reads worse than ``40``.

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
    >>> number(2.0)
    '2'
    >>> number(1.5)
    '1.5'
    >>> number(-0.25)
    '-0.25'
    """
    if value == int(value):
        return str(int(value))
    return repr(round(value, 6))
