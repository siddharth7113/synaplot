"""Draw neural network architecture diagrams with LaTeX and TikZ.

You describe a network as a list of layers and the connections between them.
synaplot turns that into TikZ code and renders it to SVG, PNG, PDF, or LaTeX
source.

Start with :class:`Diagram`, add layers from this namespace, and call
:meth:`Diagram.to_tex`. Subclass :class:`Layer` to draw something new, or
hand :func:`from_torch` a PyTorch model and draw what it did.
"""

from typing import TYPE_CHECKING

from synaplot.core.base import DrawContext, Layer
from synaplot.core.diagram import (
    Annotation,
    Connection,
    ConnectionStyle,
    Diagram,
    Group,
    Legend,
    LegendEntry,
)
from synaplot.core.geometry import Anchor, Attach, Offset, Size
from synaplot.core.theme import Theme
from synaplot.layers import (
    BatchNorm,
    Block,
    Concat,
    Conv,
    ConvRelu,
    Deconv,
    Dense,
    FullyConnected,
    Input,
    Operator,
    Pool,
    Softmax,
    Sum,
    Unpool,
)
from synaplot.text import escape

if TYPE_CHECKING:
    from synaplot.pytorch import from_torch

__version__ = "0.0.1a0"


def __getattr__(name: str) -> object:
    """Import a model reader the first time it is asked for.

    torch is optional and slow to import, so ``import synaplot`` does not
    load it; ``synaplot.from_torch`` does.
    """
    if name == "from_torch":
        from synaplot.pytorch import from_torch

        return from_torch
    raise AttributeError(f"module 'synaplot' has no attribute {name!r}")


__all__ = [
    "Anchor",
    "Annotation",
    "Attach",
    "BatchNorm",
    "Block",
    "Concat",
    "Connection",
    "ConnectionStyle",
    "Conv",
    "ConvRelu",
    "Deconv",
    "Dense",
    "Diagram",
    "DrawContext",
    "FullyConnected",
    "Group",
    "Input",
    "Layer",
    "Legend",
    "LegendEntry",
    "Offset",
    "Operator",
    "Pool",
    "Size",
    "Softmax",
    "Sum",
    "Theme",
    "Unpool",
    "__version__",
    "escape",
    "from_torch",
]
