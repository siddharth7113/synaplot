"""Draw neural network architecture diagrams with LaTeX and TikZ.

You describe a network as a list of layers and the connections between them.
synaplot turns that into TikZ code and renders it to SVG, PNG, PDF, or LaTeX
source.

Start with :class:`Diagram`, add layers from this namespace, and call
:meth:`Diagram.to_tex`.
"""

from synaplot.core.diagram import Connection, ConnectionStyle, Diagram
from synaplot.core.geometry import Anchor, Attach, Offset, Scale, Size
from synaplot.core.theme import Theme
from synaplot.layers import (
    Block,
    Concat,
    Conv,
    ConvRelu,
    Dense,
    Input,
    Operator,
    Pool,
    Softmax,
    Sum,
    Unpool,
)
from synaplot.text import escape

__version__ = "0.0.1a0"

__all__ = [
    "Anchor",
    "Attach",
    "Block",
    "Concat",
    "Connection",
    "ConnectionStyle",
    "Conv",
    "ConvRelu",
    "Dense",
    "Diagram",
    "Input",
    "Offset",
    "Operator",
    "Pool",
    "Scale",
    "Size",
    "Softmax",
    "Sum",
    "Theme",
    "Unpool",
    "__version__",
    "escape",
]
