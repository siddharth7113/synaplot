"""The layers a diagram can draw.

Each class turns a description of a network layer into one TikZ pic. Sizes are
drawing sizes in TikZ units, not tensor shapes: they control how big the box
looks, and are usually chosen so a shrinking feature map is drawn smaller.
"""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar, Literal

from pydantic import Field

from synaplot.core.base import DrawContext, Layer, label_array
from synaplot.core.geometry import Anchor, Size
from synaplot.core.theme import color_macro


class BoxLayer(Layer):
    """Base for layers drawn as one or more plain boxes.

    Parameters
    ----------
    size
        How large to draw the box.
    opacity
        How opaque the fill is, from 0 to 1.
    """

    role: ClassVar[str] = "conv"

    size: Size = Size()
    opacity: float = Field(default=0.4, ge=0, le=1)
    pic: ClassVar[str] = "Box"

    def half_height(self, scale: float) -> float:
        """Return half the drawn height of the box."""
        return self.size.height * scale / 2

    def depth_extent(self, scale: float) -> float:
        """Return how deep the box is drawn."""
        return self.size.depth * scale

    def pic_options(self, context: DrawContext) -> dict[str, str]:
        """Return the TikZ options common to every box layer."""
        return {
            "fill": self.fill_colour(context, self.role),
            "opacity": str(self.opacity),
            "height": str(self.size.height),
            "width": self.size.width_to_tikz(),
            "depth": str(self.size.depth),
        }


class FilteredBox(BoxLayer):
    r"""Base for a box labelled with its filter count and feature map size.

    Parameters
    ----------
    filters
        Number of output channels, written along the bottom edge. A list draws
        one box per entry, which is how a run of convolutions is shown as a
        single layer.
    spatial
        Size of the feature map, written along the depth edge. Free text, so
        ``'H/2'`` works as well as a number.

    """

    role: ClassVar[str] = "conv"

    filters: int | list[int] | None = None
    spatial: str | int | None = None

    def pic_options(self, context: DrawContext) -> dict[str, str]:
        """Return the TikZ options, including the filter and size labels."""
        options = super().pic_options(context)
        filters = self.filters if isinstance(self.filters, list) else [self.filters]
        options["xlabel"] = label_array(
            "" if value is None else str(value) for value in filters
        )
        if self.spatial is not None:
            options["zlabel"] = str(self.spatial)
        return options


class BandedBox(BoxLayer):
    """Base for a box with a colored band down the right of each box it draws.

    The band stands for the activation applied after the layer.

    Parameters
    ----------
    band_opacity
        How opaque the band is, from 0 to 1.

    Attributes
    ----------
    band_role : str
        Which color of the theme the band is filled with.
    """

    pic: ClassVar[str] = "RightBandedBox"
    band_role: ClassVar[str] = "conv_band"

    band_opacity: float = Field(default=0.6, ge=0, le=1)

    def pic_options(self, context: DrawContext) -> dict[str, str]:
        """Return the TikZ options for this box and its band."""
        options = super().pic_options(context)
        options["bandfill"] = f"\\{color_macro(self.band_role)}"
        options["bandopacity"] = str(self.band_opacity)
        return options


class Conv(FilteredBox):
    """A convolution, drawn as a box."""

    kind: Literal["conv"] = "conv"
    title: ClassVar[str] = "Convolution"


class ConvRelu(FilteredBox, BandedBox):
    """A convolution followed by an activation, drawn as a banded box."""

    kind: Literal["conv_relu"] = "conv_relu"
    title: ClassVar[str] = "Convolution + ReLU"


class Deconv(FilteredBox):
    """A transposed convolution, drawn as a box."""

    kind: Literal["deconv"] = "deconv"
    role: ClassVar[str] = "deconv"
    title: ClassVar[str] = "Transposed convolution"


class BatchNorm(BoxLayer):
    """A normalization layer, drawn as a thin box.

    It leaves the feature map the size it was, so it is drawn as tall and as
    deep as the layer before it and much thinner.
    """

    kind: Literal["batch_norm"] = "batch_norm"
    role: ClassVar[str] = "batchnorm"
    title: ClassVar[str] = "Batch normalization"

    size: Size = Size(width=0.7)
    opacity: float = Field(default=0.6, ge=0, le=1)


class FullyConnected(BandedBox):
    """A fully connected layer, drawn as a banded box.

    This is how a dense layer is drawn among feature maps. For a plain neural
    network drawn as columns of units, use :class:`Dense`.

    Parameters
    ----------
    units
        Number of units, written along the bottom edge.

    """

    kind: Literal["fully_connected"] = "fully_connected"
    role: ClassVar[str] = "fc"
    band_role: ClassVar[str] = "fc_band"
    title: ClassVar[str] = "Fully connected"

    size: Size = Size(width=1.5, height=3, depth=25)
    units: int | None = None

    def pic_options(self, context: DrawContext) -> dict[str, str]:
        """Return the TikZ options, including the unit count."""
        options = super().pic_options(context)
        options["xlabel"] = label_array(["" if self.units is None else str(self.units)])
        return options


class Resampling(BoxLayer):
    """Base for a layer that changes the size of a feature map."""

    size: Size = Size(width=1, height=32, depth=32)
    opacity: float = Field(default=0.5, ge=0, le=1)


class Pool(Resampling):
    """A pooling layer, drawn as a short box."""

    kind: Literal["pool"] = "pool"
    title: ClassVar[str] = "Pooling"
    role: ClassVar[str] = "pool"


class Unpool(Resampling):
    """An upsampling layer, drawn as a short box."""

    kind: Literal["unpool"] = "unpool"
    title: ClassVar[str] = "Upsampling"
    role: ClassVar[str] = "unpool"


class Softmax(BoxLayer):
    """A softmax output, drawn as a thin box.

    Parameters
    ----------
    classes
        Number of classes, written along the depth edge.

    """

    kind: Literal["softmax"] = "softmax"
    title: ClassVar[str] = "Softmax"
    role: ClassVar[str] = "softmax"

    size: Size = Size(width=1.5, height=3, depth=25)
    opacity: float = Field(default=0.8, ge=0, le=1)
    classes: int | None = None

    def pic_options(self, context: DrawContext) -> dict[str, str]:
        """Return the TikZ options for this softmax."""
        options = super().pic_options(context)
        if self.classes is not None:
            options["zlabel"] = str(self.classes)
        return options


class Ball(Layer):
    """Base for operations drawn as a sphere, such as addition.

    Parameters
    ----------
    radius
        Radius of the sphere, in TikZ units.
    opacity
        How opaque the fill is, from 0 to 1.

    Attributes
    ----------
    symbol : str
        The symbol drawn inside the sphere, as LaTeX math.
    """

    role: ClassVar[str] = "sum"
    symbol: ClassVar[str] = r"$\Sigma$"
    pic: ClassVar[str] = "Ball"

    radius: float = 2.5
    opacity: float = Field(default=0.6, ge=0, le=1)

    @property
    def anchors(self) -> frozenset[Anchor]:
        """Return the five anchors a ball defines."""
        return Anchor.ball_anchors()

    def half_height(self, scale: float) -> float:
        """Return the radius, which is half the drawn height of a sphere."""
        return self.radius * scale

    def depth_extent(self, scale: float) -> float:
        """Return how deep the sphere is drawn."""
        return 2 * self.radius * scale

    def pic_options(self, context: DrawContext) -> dict[str, str]:
        """Return the TikZ options for this sphere."""
        return {
            "fill": self.fill_colour(context, self.role),
            "opacity": str(self.opacity),
            "radius": str(self.radius),
            "logo": self.symbol,
        }


class Sum(Ball):
    r"""An elementwise sum, drawn as a sphere marked with a plus."""

    kind: Literal["sum"] = "sum"
    title: ClassVar[str] = "Sum"
    role: ClassVar[str] = "sum"
    symbol: ClassVar[str] = "$+$"


class Concat(Ball):
    r"""A concatenation, drawn as a sphere marked with two bars."""

    kind: Literal["concat"] = "concat"
    title: ClassVar[str] = "Concatenation"
    role: ClassVar[str] = "concat"
    symbol: ClassVar[str] = "$||$"


class Input(Layer):
    r"""An image drawn as a flat plane, used to show the input to a network.

    The plane stands across the depth axis, so its height is drawn up the page
    and its width towards the reader.

    Parameters
    ----------
    path
        Path to the image. A relative path is read relative to the directory
        you render from, and the file is copied in beside the LaTeX source, so
        the same path works whatever directory the compiler runs in.
    width, height
        Size of the plane, in centimetres.

    """

    pic: ClassVar[str] = ""
    flat: ClassVar[bool] = True

    kind: Literal["input"] = "input"
    title: ClassVar[str] = ""

    path: str
    width: float = 8.0
    height: float = 8.0

    @property
    def anchors(self) -> frozenset[Anchor]:
        """Return the seven anchors an image plane defines."""
        return Anchor.plane_anchors()

    def assets(self) -> list[Path]:
        """Return the image, so that rendering copies it in beside the source."""
        return [Path(self.path)]

    def half_height(self, scale: float) -> float:
        """Return half the height of the plane, which is given in centimetres."""
        return self.height / 2

    def depth_extent(self, scale: float) -> float:
        """Return the width of the plane, which is drawn along the depth axis."""
        return self.width

    def pic_options(self, context: DrawContext) -> dict[str, str]:
        """Return an empty mapping. An image is drawn as a node, not a pic."""
        return {}

    def to_tikz(self, context: DrawContext) -> str:
        """Return the node that draws the image, and the anchors it defines.

        A node names its own anchors with a dot, as in ``(img.east)``, while
        every layer in a diagram is addressed with a hyphen. The coordinates
        are written out so that an image can be chained from and connected to
        like any other layer.
        """
        at = context.attach.to_tikz() if context.attach else "(0,0,0)"
        point = at[1:-1]
        offsets = {
            Anchor.ANCHOR: (0.0, 0.0),
            Anchor.EAST: (0.0, 0.0),
            Anchor.WEST: (0.0, 0.0),
            Anchor.NORTH: (self.height / 2, 0.0),
            Anchor.SOUTH: (-self.height / 2, 0.0),
            Anchor.NEAR: (0.0, self.width / 2),
            Anchor.FAR: (0.0, -self.width / 2),
        }
        lines = [
            # The depth axis runs to the lower left, so the plane's own x axis
            # runs the same way and the image comes out mirrored. Reflecting it
            # once puts it back.
            f"\\node[canvas is zy plane at x=0] ({self.name}-plane) at {at}\n"
            f"    {{\\reflectbox{{\\includegraphics[width={self.width:g}cm,"
            f"height={self.height:g}cm]{{{self.path}}}}}}};"
        ]
        lines += [
            f"\\coordinate ({self.name}-{anchor.value}) at "
            f"([shift={{(0,{up:g},{out:g})}}] {point});"
            for anchor, (up, out) in offsets.items()
        ]
        return "\n".join(lines)


class Dense(Layer):
    """A fully connected layer, drawn as a column of circles.

    This is how a plain neural network is usually shown. A wide layer would be
    unreadable with one circle per unit, so ``nodes`` sets how many to draw and
    ``break_after`` marks where the rest were left out.

    Parameters
    ----------
    units
        How many units the layer really has. Written under the layer when no
        caption is given.
    nodes
        How many circles to draw.
    break_after
        Draw a vertical ellipsis after this circle, standing for the units not
        drawn. ``None`` draws none.
    break_gap
        Extra room to leave for that ellipsis, in TikZ units, on top of the
        usual distance between two circles.
    radius
        Radius of each circle, in TikZ units.
    spacing
        Distance between the centres of two circles, in TikZ units.
    opacity
        How opaque the fill is, from 0 to 1.
    """

    kind: Literal["dense"] = "dense"
    title: ClassVar[str] = "Fully connected"
    role: ClassVar[str] = "fc"
    pic: ClassVar[str] = "NodeLayer"
    flat: ClassVar[bool] = True

    units: int | None = None
    nodes: int = Field(default=4, ge=1)
    break_after: int | None = None
    break_gap: float = 3.0
    radius: float = 1.6
    spacing: float = 5.0
    opacity: float = Field(default=0.7, ge=0, le=1)

    @property
    def anchors(self) -> frozenset[Anchor]:
        """Return the nine anchors a flat column defines."""
        return Anchor.flat_anchors()

    def node_names(self) -> list[str]:
        """Return a suffix per circle, so an edge can reach each one."""
        return [str(index) for index in range(1, self.nodes + 1)]

    def half_height(self, scale: float) -> float:
        """Return half the height of the column, including the outer circles."""
        gap = self.break_gap if self.break_after is not None else 0.0
        return (((self.nodes - 1) * self.spacing + gap) / 2 + self.radius) * scale

    def pic_options(self, context: DrawContext) -> dict[str, str]:
        """Return the TikZ options for this column."""
        options = {
            "count": str(self.nodes),
            "radius": str(self.radius),
            "spacing": str(self.spacing),
            "fill": self.fill_colour(context, self.role),
            "opacity": str(self.opacity),
        }
        if self.break_after is not None:
            options["break"] = str(self.break_after)
            options["breakgap"] = str(self.break_gap)
        if not self.caption and self.units is not None:
            options["caption"] = str(self.units)
        return options


class Operator(Layer):
    r"""An operation on two paths, drawn as a small circle holding a symbol.

    This is how a drawing marks the point where a residual path rejoins the
    one it left, and it is drawn flat on the page so that it sits among
    :class:`Block` layers rather than among feature maps. For the same
    operation drawn as a shaded sphere beside 3D feature maps, use :class:`Sum`
    or :class:`Concat`.

    Parameters
    ----------
    symbol
        What to draw inside the circle. Read as LaTeX, so ``r"$\otimes$"``
        draws a multiplication sign.
    radius
        Radius of the circle, in TikZ units.
    opacity
        How opaque the fill is, from 0 to 1.
    """

    kind: Literal["operator"] = "operator"
    role: ClassVar[str] = "sum"
    pic: ClassVar[str] = "FlatOperator"
    flat: ClassVar[bool] = True

    symbol: str = "$+$"
    radius: float = 3.0
    opacity: float = Field(default=0.7, ge=0, le=1)

    @property
    def anchors(self) -> frozenset[Anchor]:
        """Return the five anchors a circle defines."""
        return Anchor.ball_anchors()

    def half_height(self, scale: float) -> float:
        """Return the radius, which is half the drawn height of a circle."""
        return self.radius * scale

    def pic_options(self, context: DrawContext) -> dict[str, str]:
        """Return the TikZ options for this operator."""
        return {
            "fill": self.fill_colour(context, self.role),
            "opacity": str(self.opacity),
            "radius": str(self.radius),
            "symbol": self.symbol,
        }


class Block(Layer):
    r"""A rounded rectangle holding a line of text.

    This is how the parts of a transformer or a recurrent cell are usually
    shown: a stack of named blocks rather than a row of feature maps.

    Parameters
    ----------
    text
        What to write inside the block. Read as LaTeX. Use ``\\\\`` to break a
        line.
    width, height
        Size of the block, in TikZ units.
    corner
        How round the corners are, in points.
    opacity
        How opaque the fill is, from 0 to 1.
    """

    kind: Literal["block"] = "block"
    role: ClassVar[str] = "conv"
    pic: ClassVar[str] = "FlatBlock"
    flat: ClassVar[bool] = True

    text: str = ""
    width: float = 40.0
    height: float = 12.0
    corner: float = 3.0
    opacity: float = Field(default=0.7, ge=0, le=1)

    @property
    def anchors(self) -> frozenset[Anchor]:
        """Return the nine anchors a flat block defines."""
        return Anchor.flat_anchors()

    def half_height(self, scale: float) -> float:
        """Return half the drawn height of the block."""
        return self.height * scale / 2

    def pic_options(self, context: DrawContext) -> dict[str, str]:
        """Return the TikZ options for this block."""
        return {
            "text": self.text,
            "width": str(self.width),
            "height": str(self.height),
            "corner": str(self.corner),
            "fill": self.fill_colour(context, self.role),
            "opacity": str(self.opacity),
        }


__all__ = [
    "Ball",
    "BandedBox",
    "BatchNorm",
    "Block",
    "BoxLayer",
    "Concat",
    "Conv",
    "ConvRelu",
    "Deconv",
    "Dense",
    "FilteredBox",
    "FullyConnected",
    "Input",
    "Operator",
    "Pool",
    "Resampling",
    "Softmax",
    "Sum",
    "Unpool",
]
