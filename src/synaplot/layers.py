"""The layers a diagram can draw.

Each class turns a description of a network layer into one TikZ pic. Sizes are
drawing sizes in TikZ units, not tensor shapes: they control how big the box
looks, and are usually chosen so a shrinking feature map is drawn smaller.
"""

from __future__ import annotations

from typing import ClassVar

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

    def pic_options(self, context: DrawContext) -> dict[str, str]:
        """Return the TikZ options common to every box layer."""
        return {
            "fill": f"\\{color_macro(self.role)}",
            "opacity": str(self.opacity),
            "height": str(self.size.height),
            "width": self.size.width_to_tikz(),
            "depth": str(self.size.depth),
        }


class Conv(BoxLayer):
    r"""A convolution, drawn as a box.

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
        """Return the TikZ options for this convolution."""
        options = super().pic_options(context)
        filters = self.filters if isinstance(self.filters, list) else [self.filters]
        options["xlabel"] = label_array(
            "" if value is None else str(value) for value in filters
        )
        if self.spatial is not None:
            options["zlabel"] = str(self.spatial)
        return options


class ConvRelu(Conv):
    r"""A convolution followed by an activation, drawn as a banded box.

    The band on the right of each box stands for the activation.

    Parameters
    ----------
    band_opacity
        How opaque the band is, from 0 to 1.

    """

    pic: ClassVar[str] = "RightBandedBox"

    band_opacity: float = Field(default=0.6, ge=0, le=1)

    def pic_options(self, context: DrawContext) -> dict[str, str]:
        """Return the TikZ options for this convolution and its band."""
        options = super().pic_options(context)
        options["bandfill"] = f"\\{color_macro('conv_relu')}"
        options["bandopacity"] = str(self.band_opacity)
        return options


class Pool(BoxLayer):
    r"""A pooling layer, drawn as a short box."""

    role: ClassVar[str] = "pool"

    size: Size = Size(width=1, height=32, depth=32)
    opacity: float = Field(default=0.5, ge=0, le=1)


class Unpool(Pool):
    """An upsampling layer, drawn as a short box in the unpool color."""

    role: ClassVar[str] = "unpool"


class Softmax(BoxLayer):
    """A softmax output, drawn as a thin box.

    Parameters
    ----------
    classes
        Number of classes, written along the depth edge.

    """

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

    def pic_options(self, context: DrawContext) -> dict[str, str]:
        """Return the TikZ options for this sphere."""
        return {
            "fill": f"\\{color_macro(self.role)}",
            "opacity": str(self.opacity),
            "radius": str(self.radius),
            "logo": self.symbol,
        }


class Sum(Ball):
    r"""An elementwise sum, drawn as a sphere marked with a plus."""

    role: ClassVar[str] = "sum"
    symbol: ClassVar[str] = "$+$"


class Concat(Ball):
    r"""A concatenation, drawn as a sphere marked with two bars."""

    role: ClassVar[str] = "concat"
    symbol: ClassVar[str] = "$||$"


class Input(Layer):
    r"""An image drawn as a flat plane, used to show the input to a network.

    Parameters
    ----------
    path
        Path to the image, as LaTeX will resolve it. Relative paths are read
        relative to the directory the document is compiled in.
    width, height
        Size of the plane, in centimetres.

    """

    pic: ClassVar[str] = ""

    path: str
    width: float = 8.0
    height: float = 8.0

    @property
    def anchors(self) -> frozenset[Anchor]:
        """Return no anchors. An image plane is a node, not a pic."""
        return frozenset()

    def half_height(self, scale: float) -> float:
        """Return half the height of the image plane, which is given in centimetres."""
        return self.height / 2

    def pic_options(self, context: DrawContext) -> dict[str, str]:
        """Return an empty mapping. An image is drawn as a node, not a pic."""
        return {}

    def to_tikz(self, context: DrawContext) -> str:
        """Return the TikZ node that draws the image."""
        at = context.attach.to_tikz() if context.attach else "(0,0,0)"
        return (
            f"\\node[canvas is zy plane at x=0] ({self.name}) at {at}\n"
            f"    {{\\includegraphics[width={self.width:g}cm,"
            f"height={self.height:g}cm]{{{self.path}}}}};"
        )


__all__ = [
    "Ball",
    "BoxLayer",
    "Concat",
    "Conv",
    "ConvRelu",
    "Input",
    "Pool",
    "Softmax",
    "Sum",
    "Unpool",
]
