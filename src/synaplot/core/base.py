"""The base class every layer derives from, and the helpers that draw one."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar

from pydantic import BaseModel

from synaplot.core.geometry import Anchor, Attach
from synaplot.core.theme import Theme

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping


@dataclass(frozen=True)
class DrawContext:
    """Diagram-wide settings passed to a layer while it is being drawn.

    Attributes
    ----------
    theme : Theme
        Colors for the diagram. A layer reads the color for its own role.
    scale : float
        Multiplier applied to every size in the diagram.
    attach : Attach or None
        Resolved position for the layer being drawn. ``None`` places it at the
        origin, which is what happens for the first layer in a diagram.
    """

    theme: Theme
    scale: float
    attach: Attach | None


class Layer(BaseModel, ABC):
    r"""A single drawn element of a diagram.

    Subclasses set :attr:`pic` to the TikZ pic they draw with and implement
    :meth:`pic_options`.

    Parameters
    ----------
    name
        Identifies the layer. Connections refer to layers by name, and the name
        becomes part of the TikZ coordinates the layer defines, so it must be
        unique within a diagram.
    to
        Where to place this layer. When it is ``None``, the diagram places the
        layer after the one before it.
    caption
        Text drawn under the layer. Read as LaTeX, so ``$3\times3$`` renders as
        math. Pass text you did not write through :func:`synaplot.escape` first.

    Attributes
    ----------
    pic : str
        Name of the TikZ pic this class draws with, such as ``'Box'``.
    """

    pic: ClassVar[str] = ""

    name: str
    to: Attach | None = None
    caption: str = ""

    @property
    def anchors(self) -> frozenset[Anchor]:
        """Return the anchors this layer defines."""
        return frozenset(Anchor)

    def half_height(self, scale: float) -> float:
        """Return half the drawn height of this layer.

        A skip arrow runs above every layer it passes, so the writer needs to
        know how tall the tallest layer is. Layers sit centered on the axis, so
        half the height is the distance from the axis to the top.

        Parameters
        ----------
        scale
            The diagram's scale.

        Returns
        -------
        float
            Distance from the axis to the top of the layer, in TikZ units.
        """
        return 0.0

    @abstractmethod
    def pic_options(self, context: DrawContext) -> dict[str, str]:
        """Return the TikZ options for this layer's pic.

        Parameters
        ----------
        context
            Diagram-wide settings, including the theme to take colors from.

        Returns
        -------
        dict of str to str
            TikZ keys and values, already formatted for LaTeX. The ``name`` and
            ``caption`` keys are added by :meth:`to_tikz`.
        """

    def to_tikz(self, context: DrawContext) -> str:
        r"""Return the TikZ that draws this layer.

        Parameters
        ----------
        context
            Diagram-wide settings, including where to place the layer.

        Returns
        -------
        str
            One TikZ ``\pic`` statement.
        """
        options = {"name": self.name, **self.pic_options(context)}
        if self.caption:
            options["caption"] = self.caption
        return draw_pic(self.pic, options, context.attach)


def draw_pic(
    pic: str,
    options: Mapping[str, str],
    attach: Attach | None,
) -> str:
    r"""Return a TikZ ``\\pic`` statement.

    Parameters
    ----------
    pic
        Name of the TikZ pic, such as ``'Box'``.
    options
        TikZ keys and values passed to the pic.
    attach
        Where to place the pic. ``None`` places it at the origin.

    Returns
    -------
    str
        A complete ``\pic`` statement, ending in a semicolon.

    Examples
    --------
    >>> print(draw_pic("Ball", {"name": "sum1"}, None))
    \pic[shift={(0,0,0)}] at (0,0,0)
        {Ball={
            name=sum1
        }};

    >>> from synaplot.core.geometry import Attach, Offset
    >>> at = Attach(layer="conv1", offset=Offset(x=2))
    >>> print(draw_pic("Box", {"name": "pool1"}, at))
    \pic[shift={(2,0,0)}] at (conv1-east)
        {Box={
            name=pool1
        }};
    """
    shift = attach.offset.to_tikz() if attach else "(0,0,0)"
    at = attach.to_tikz() if attach else "(0,0,0)"
    body = ",\n        ".join(f"{key}={value}" for key, value in options.items())
    return (
        f"\\pic[shift={{{shift}}}] at {at}\n    {{{pic}={{\n        {body}\n    }}}};"
    )


def label_array(labels: Iterable[str]) -> str:
    """Return labels in the array form a box pic expects for ``xlabel``.

    A box draws one label per box in its width and reads them by index. A
    one-element array does not parse, so a second empty entry is added.

    Parameters
    ----------
    labels
        One label per box, in drawing order.

    Returns
    -------
    str
        A braced TikZ array of quoted labels.

    Examples
    --------
    >>> label_array(["64"])
    '{{"64",""}}'
    >>> label_array(["64", "128", "256"])
    '{{"64","128","256"}}'
    >>> label_array([])
    '{{"",""}}'
    """
    items = list(labels)
    if not items:
        items = [""]
    if len(items) == 1:
        items.append("")
    return "{{" + ",".join(f'"{item}"' for item in items) + "}}"
