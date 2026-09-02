"""Draw a diagram from a PyTorch model.

The model runs once on a sample input while forward hooks and a
:class:`~torch.overrides.TorchFunctionMode` record every module call and
every operation between modules, with the tensors each consumed and
produced. That record is a :class:`Trace`. :func:`from_torch` picks the calls
to draw for a depth, works out which fed which, turns each into a layer
through :func:`layer_for`, sizes it from its tensors through
:class:`Sizing`, and returns the :class:`~synaplot.Diagram`, which you can
then edit, or write out as YAML to finish by hand.

Teach it a module of your own by registering a handler::

    from synaplot.pytorch import Call, layer_for

    @layer_for.register
    def _(module: MyAttention, call: Call) -> sp.Layer | None:
        return sp.Block(name=call.name, text="attention")

This module needs torch: ``pip install synaplot[torch]``.
"""

from __future__ import annotations

import math
import re
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from functools import singledispatch
from pathlib import Path
from typing import Any, TypeAlias

import torch
from pydantic import BaseModel
from torch import Tensor, nn
from torch.overrides import TorchFunctionMode

from synaplot.core.base import Layer
from synaplot.core.diagram import Diagram
from synaplot.core.geometry import Size
from synaplot.layers import (
    BatchNorm,
    Block,
    Concat,
    Conv,
    ConvRelu,
    Deconv,
    FullyConnected,
    Input,
    Pool,
    Softmax,
    Sum,
    Unpool,
)
from synaplot.text import escape

__all__ = [
    "Call",
    "Inputs",
    "Shape",
    "Sizing",
    "Trace",
    "from_torch",
    "layer_for",
    "trace",
]

Shape: TypeAlias = tuple[int, ...]
"""The shape of a tensor."""

Inputs: TypeAlias = Tensor | tuple[Tensor, ...] | Mapping[str, Tensor]
"""What a model is run on: one tensor, several, or keyword arguments."""


@dataclass(eq=False)
class Call:
    """One thing the model did while it ran.

    A call is a module's forward, an operation between modules such as
    ``torch.cat``, or the model's own input, which is the first call of every
    trace and produces the tensors the model was given.

    Attributes
    ----------
    path : str
        The module's attribute path, such as ``layer1.0.conv1``, or the name
        of the function for an operation, or ``input``.
    name : str
        The path as a layer name: anything TikZ cannot use becomes an
        underscore, and a module called more than once gets ``_2``, ``_3``,
        and so on.
    module : torch.nn.Module or None
        The module, or ``None`` for an operation or the input.
    parent : Call or None
        The call this one happened inside. ``None`` for the model and its
        input.
    depth : int
        How many modules enclose this one. The model is 0 and its children
        are 1.
    leaf : bool
        Whether the module has no children. An operation counts as a leaf.
    inputs, outputs : list of tuple of int
        The shape of each tensor consumed and produced.
    consumed, produced : list of int
        The identity of each of those tensors, which is how a trace works out
        which call fed which.
    size : Size or None
        The drawing size given to the output, once a :class:`Sizing` has been
        applied. A box for a feature map, a bar for anything else.
    """

    path: str
    name: str
    module: nn.Module | None
    parent: Call | None
    depth: int
    leaf: bool
    inputs: list[Shape] = field(default_factory=list)
    outputs: list[Shape] = field(default_factory=list)
    consumed: list[int] = field(default_factory=list)
    produced: list[int] = field(default_factory=list)
    size: Size | None = None

    @property
    def feature_map(self) -> Shape | None:
        """Return the output's shape when it is a feature map, else ``None``.

        A feature map has a batch, channels, and at least two spatial axes.
        """
        shape = self.outputs[0] if self.outputs else None
        return shape if shape is not None and len(shape) >= 4 else None


def _tensors(value: object) -> list[Tensor]:
    """Return every tensor in a value, however deep in tuples, lists, and dicts."""
    if isinstance(value, Tensor):
        return [value]
    if isinstance(value, Mapping):
        value = list(value.values())
    if isinstance(value, list | tuple):
        return [tensor for item in value for tensor in _tensors(item)]
    return []


class _Recorder(TorchFunctionMode):  # type: ignore[misc]  # torch is untyped here
    """Records module calls, and the operations between them, as a model runs."""

    def __init__(self) -> None:
        super().__init__()
        self.calls: list[Call] = []
        # Modules whose forward is running, outermost first.
        self.open: list[Call] = []
        # How many calls have taken each layer name, so that a repeat is told
        # apart from the first.
        self.taken: dict[str, int] = {}
        # Every tensor met, held so that no id is reused while tracing.
        self.kept: list[Tensor] = []

    def __torch_function__(
        self,
        func: Callable[..., Any],
        types: Iterable[type],
        args: tuple[Any, ...] = (),
        kwargs: dict[str, Any] | None = None,
    ) -> Any:
        """Run one torch function, and record it when it ran between modules."""
        kwargs = kwargs or {}
        result = func(*args, **kwargs)
        # An operation inside a leaf module is that module's own business.
        if self.open and not self.open[-1].leaf and _tensors(result):
            name = getattr(func, "__name__", str(func))
            self.finish(self.start(name, None, (args, kwargs)), result)
        return result

    def start(self, path: str, module: nn.Module | None, arguments: object) -> Call:
        """Return a new call that has consumed its arguments and not yet finished."""
        base = re.sub(r"[^A-Za-z0-9-]+", "_", path).strip("_") or "op"
        count = self.taken[base] = self.taken.get(base, 0) + 1
        consumed = _tensors(arguments)
        return Call(
            path=path,
            name=base if count == 1 else f"{base}_{count}",
            module=module,
            parent=self.open[-1] if self.open else None,
            depth=len(self.open),
            leaf=module is None or not any(module.children()),
            inputs=[tuple(tensor.shape) for tensor in consumed],
            consumed=[id(tensor) for tensor in consumed],
        )

    def finish(self, call: Call, output: object) -> None:
        """Record what a call produced, and add it to the trace."""
        produced = _tensors(output)
        self.kept += produced
        call.outputs = [tuple(tensor.shape) for tensor in produced]
        call.produced = [id(tensor) for tensor in produced]
        self.calls.append(call)

    def enter(self, path: str, module: nn.Module, arguments: object) -> None:
        """Note that a module's forward has begun."""
        self.open.append(self.start(path, module, arguments))

    def leave(self, output: object) -> None:
        """Note that the innermost module's forward has returned."""
        self.finish(self.open.pop(), output)


def _arguments(inputs: Inputs) -> tuple[tuple[Tensor, ...], dict[str, Tensor]]:
    """Return the sample input as the arguments the model is called with."""
    if isinstance(inputs, Mapping):
        return (), dict(inputs)
    if isinstance(inputs, tuple):
        return inputs, {}
    return (inputs,), {}


@dataclass
class Trace:
    """What a model did on one input.

    Attributes
    ----------
    calls : list of Call
        The model's input first, then each call as it finished, so that a
        call comes after everything that fed it.
    """

    calls: list[Call]

    @property
    def largest(self) -> int:
        """Return the spatial size of the largest feature map in the trace."""
        return max(
            (
                shape[-1]
                for call in self.calls
                for shape in call.outputs
                if len(shape) >= 4
            ),
            default=1,
        )

    def drawn(self, depth: int | None) -> list[Call]:
        """Return the module calls to draw at a depth.

        Parameters
        ----------
        depth
            How far into the module tree to draw. The modules at that depth
            are drawn, and so is a leaf above it, since nothing below it could
            stand in for it. ``None`` draws every leaf.

        Returns
        -------
        list of Call
            The calls, in the order they finished.
        """
        modules = [
            call for call in self.calls if call.module is not None and call.depth
        ]
        if depth is None:
            return [call for call in modules if call.leaf]
        return [c for c in modules if c.depth == depth or (c.leaf and c.depth < depth)]

    def feeds(self, chosen: Sequence[Call]) -> dict[Call, list[Call]]:
        """Return what feeds each call, among the chosen ones and what lies between.

        An operation inside a chosen module belongs to that module and is not
        seen. One outside runs between chosen modules, as ``torch.cat`` does
        in a U-Net, so it is seen, and so is the model's input.

        Parameters
        ----------
        chosen
            The module calls to draw.

        Returns
        -------
        dict of Call to list of Call
            Each seen call, in the order they finished, to the seen calls that
            produced what it consumed, in the order it consumed them.
        """
        inside = set(chosen)
        seen = [
            call
            for call in self.calls
            if call in inside or (call.module is None and not _within(call, inside))
        ]
        producer: dict[int, Call] = {}
        feeds: dict[Call, list[Call]] = {}
        for call in seen:
            sources = [producer[t] for t in call.consumed if t in producer]
            feeds[call] = list(dict.fromkeys(sources))
            producer.update((t, call) for t in call.produced)
        return feeds


def _within(call: Call, modules: set[Call]) -> bool:
    """Return whether a call happened inside any of those module calls."""
    parent = call.parent
    while parent is not None:
        if parent in modules:
            return True
        parent = parent.parent
    return False


def trace(model: nn.Module, inputs: Inputs) -> Trace:
    """Run a model once and record what it did.

    The model is run in evaluation mode with gradients off, and put back in
    the mode it was in. Nothing about it is changed.

    Parameters
    ----------
    model
        The model to run.
    inputs
        What to run it on: one tensor, a tuple of positional arguments, or a
        mapping of keyword arguments.

    Returns
    -------
    Trace
        Every module call and every operation between modules, in the order
        each finished.
    """
    args, kwargs = _arguments(inputs)
    recorder = _Recorder()
    origin = recorder.start("input", None, ())
    recorder.finish(origin, (args, kwargs))
    handles = [
        handle
        for path, module in model.named_modules()
        for handle in (
            module.register_forward_pre_hook(
                lambda m, a, k, path=path: recorder.enter(
                    path or type(m).__name__, m, (a, k)
                ),
                with_kwargs=True,
            ),
            module.register_forward_hook(lambda m, a, o: recorder.leave(o)),
        )
    ]
    training = model.training
    try:
        with torch.no_grad(), recorder:
            model.eval()(*args, **kwargs)
    finally:
        for handle in handles:
            handle.remove()
        model.train(training)
    return Trace(recorder.calls)


class Sizing(BaseModel):
    """How a tensor's shape becomes a drawing size.

    The rule is a logarithm. A feature map is drawn ``per_halving`` units
    shorter each time it is half the size of the largest map in the model,
    which is drawn at ``tallest``, and a box gains a unit of width for each
    doubling of its channels past 32. PlotNeuralNet's hand-picked VGG16 sizes
    fit this within a unit. Anything that is not a feature map gets a bar,
    as a fully connected layer is drawn, as long as the logarithm of its width.

    Parameters
    ----------
    tallest
        Height and depth of the largest feature map, in drawing units.
    per_halving
        How much shorter a map is drawn each time it halves.
    smallest
        The floor, so that a 1 by 1 map is still visible.
    thinnest
        Width of a box with 32 channels or fewer.
    longest
        Length of the bar drawn for 4096 units.

    Examples
    --------
    >>> Sizing().box((1, 64, 112, 112), largest=224)
    Size(width=2.0, height=34.0, depth=34.0)
    >>> Sizing().bar(4096).depth
    30.0
    """

    tallest: float = 40.0
    per_halving: float = 6.0
    smallest: float = 4.0
    thinnest: float = 1.0
    longest: float = 30.0

    def box(self, shape: Shape, largest: int) -> Size:
        """Return the box for a feature map of that shape.

        Parameters
        ----------
        shape
            The map's shape: batch, channels, then its spatial axes.
        largest
            The spatial size of the largest map in the model.
        """
        halvings = math.log2(max(largest / shape[-1], 1))
        side = max(self.smallest, self.tallest - self.per_halving * halvings)
        width = max(self.thinnest, self.thinnest + math.log2(max(shape[1], 1)) - 5)
        return Size(width=width, height=side, depth=side)

    def bar(self, units: int) -> Size:
        """Return the bar for a layer of that many units."""
        length = max(2 * self.smallest, self.longest * math.log2(max(units, 2)) / 12)
        return Size(width=1.5, height=3, depth=length)


@singledispatch
def layer_for(module: nn.Module, call: Call) -> Layer | None:
    """Return the layer that draws a module, or ``None`` to draw nothing.

    Dispatches on the module's class, so a handler registered for a class
    covers its subclasses. Register one for a module of your own with
    ``@layer_for.register``; it receives the module and its :class:`Call`,
    whose ``name`` is safe to name a layer with and whose ``size`` is the
    drawing size its output was given. Return ``None`` and the module is not
    drawn, with arrows passing through it to whatever it fed.

    The default handler reads the tensors rather than the class, so it covers
    modules it has never heard of. A module that turned a feature map into a
    smaller one with the same channels, and had nothing to learn, is drawn as
    pooling, and into a larger one as upsampling. Any other module that
    produced a feature map is drawn as a convolution box labelled with what
    it produced, which is how a whole stage of a network is drawn when the
    depth stops at it. A module whose output is not a feature map is drawn
    as a block carrying its name, unless it is a leaf with nothing to learn,
    such as a flatten or a dropout. A leaf that left its input as it was,
    such as an activation, is not drawn either; one that follows a
    convolution becomes the band on that box.

    Parameters
    ----------
    module
        The module that ran.
    call
        Its call, with the shapes it consumed and produced.

    Returns
    -------
    Layer or None
        The layer to draw, or ``None`` to draw nothing.
    """
    learns = any(True for _ in module.parameters())
    after = call.feature_map
    if after is None:
        if call.leaf and not learns:
            return None
        return Block(name=call.name, text=escape(call.path))
    before = call.inputs[0] if call.inputs else after
    resampled = len(before) == len(after) and before[1] == after[1]
    if resampled and before[-1] != after[-1] and not learns:
        kind = Pool if after[-1] < before[-1] else Unpool
        return kind(name=call.name, size=_resized(call, width=1.0))
    if call.leaf and not learns and before == after:
        return None
    return Conv(name=call.name, filters=after[1], spatial=after[-1], size=call.size)


def _resized(call: Call, width: float) -> Size:
    """Return the call's size with the width a thin layer is drawn at."""
    size = call.size or Size()
    return size.model_copy(update={"width": width})


@layer_for.register(nn.Conv1d)
@layer_for.register(nn.Conv2d)
@layer_for.register(nn.Conv3d)
def _conv(module: nn.Module, call: Call) -> Layer:
    shape = call.outputs[0]
    return Conv(name=call.name, filters=shape[1], spatial=shape[-1], size=call.size)


@layer_for.register(nn.ConvTranspose1d)
@layer_for.register(nn.ConvTranspose2d)
@layer_for.register(nn.ConvTranspose3d)
def _deconv(module: nn.Module, call: Call) -> Layer:
    shape = call.outputs[0]
    return Deconv(name=call.name, filters=shape[1], spatial=shape[-1], size=call.size)


@layer_for.register(nn.BatchNorm2d)
@layer_for.register(nn.BatchNorm3d)
@layer_for.register(nn.GroupNorm)
@layer_for.register(nn.InstanceNorm2d)
def _norm(module: nn.Module, call: Call) -> Layer | None:
    # Normalizing a feature map is drawn as a thin box beside it; normalizing
    # anything else is not worth a shape of its own.
    if call.feature_map is None:
        return None
    return BatchNorm(name=call.name, size=_resized(call, width=0.7))


@layer_for.register(nn.Linear)
def _linear(module: nn.Module, call: Call) -> Layer:
    units = call.outputs[0][-1]
    return FullyConnected(name=call.name, units=units, size=call.size)


@layer_for.register(nn.Softmax)
@layer_for.register(nn.LogSoftmax)
def _softmax(module: nn.Module, call: Call) -> Layer:
    return Softmax(name=call.name, classes=call.outputs[0][-1], size=call.size)


def _activation(module: nn.Module | None) -> bool:
    """Return whether a module is one of torch's activations.

    They are the classes torch defines in its activation module, which is a
    rule rather than a list, so a new one counts the day it is added.
    """
    return module is not None and type(module).__module__ == nn.ReLU.__module__


def _join(call: Call) -> Layer | None:
    """Return the ball an operation between modules is drawn as, if any.

    An addition of two tensors is a sum and a concatenation is a concat,
    which is how a residual path or a skip connection is shown rejoining the
    trunk. Any other operation, such as a flatten, is not drawn.
    """
    if call.module is not None or len(call.consumed) < 2:
        return None
    if call.path.strip("_") in ("add", "iadd", "radd"):
        return Sum(name=call.name)
    if call.path in ("cat", "concat", "concatenate"):
        return Concat(name=call.name)
    return None


def _read_image(path: str | Path) -> Tensor:
    """Return an image as the tensor a vision model takes.

    One image, channels first, as floats from 0 to 1, with no other
    preprocessing. A model that wants its input normalized is given the
    tensor directly instead.
    """
    try:
        from PIL import Image
    except ImportError:
        raise ImportError(
            "reading an image needs Pillow; install it, or read the image "
            "yourself and pass the tensor as inputs"
        ) from None
    with Image.open(path) as opened:
        image = opened.convert("RGB")
    pixels = torch.frombuffer(bytearray(image.tobytes()), dtype=torch.uint8)
    channels_last = pixels.view(image.height, image.width, 3)
    return channels_last.permute(2, 0, 1).float().div(255).unsqueeze(0)


def from_torch(
    model: nn.Module,
    inputs: Inputs | None = None,
    *,
    image: str | Path | None = None,
    depth: int | None = 3,
    name: str | None = None,
    sizing: Sizing | None = None,
    captions: Callable[[Call], str] | None = None,
) -> Diagram:
    """Draw a diagram of a PyTorch model.

    The model runs once on the sample input, and what it did is drawn: each
    module as a layer sized and labelled by the tensor it produced, an
    addition or a concatenation between modules as the ball a residual path
    rejoins at, and an arrow from each layer to what it fed. Layers are
    chained in the order they ran, so nothing needs a position.

    Parameters
    ----------
    model
        The model to draw.
    inputs
        What to run it on: one tensor, a tuple of positional arguments, or a
        mapping of keyword arguments, which is how a Hugging Face model is
        called. Required unless ``image`` is given.
    image
        A picture to draw at the start of the diagram, as an input layer.
        Given without ``inputs``, it is also what the model runs on, read
        with Pillow as floats from 0 to 1 and nothing else done to it.
    depth
        How far into the module tree to draw. The modules at that depth are
        drawn as one layer each, and so is a leaf above it. ``1`` draws the
        model's direct children, which for a ResNet is one box per stage.
        ``None`` draws every leaf. The default of 3 is torchinfo's.
    name
        The diagram's name, and so its default file name. Defaults to the
        model's class name in lower case.
    sizing
        How shapes become drawing sizes. Defaults to :class:`Sizing`.
    captions
        Returns the caption for a call. Defaults to the module's attribute
        path, escaped for LaTeX.

    Returns
    -------
    Diagram
        The drawing, ready to save, edit, or write out as a specification.

    Raises
    ------
    ValueError
        If neither ``inputs`` nor ``image`` is given.

    Notes
    -----
    A residual added onto the model's own input is drawn only when the input
    is drawn, which is what ``image`` does. Every leaf of a deep network is a
    valid drawing and an unreadable figure, which is what ``depth`` is for.
    """
    if inputs is None:
        if image is None:
            raise ValueError("from_torch needs inputs to run the model on, or an image")
        inputs = _read_image(image)
    sizing = sizing or Sizing()
    caption = captions or (lambda call: escape(call.path))

    traced = trace(model, inputs)
    for call in traced.calls:
        if call.outputs:
            shape = call.outputs[0]
            call.size = (
                sizing.box(shape, traced.largest)
                if call.feature_map
                else sizing.bar(shape[-1])
            )

    diagram = Diagram(name=name or type(model).__name__.lower())
    # Each seen call, to the name of the layer standing for it: its own, or
    # for a call that is not drawn, the layer that fed it.
    standing: dict[Call, str] = {}
    if image is not None:
        diagram.add(Input(name="input", path=str(image)))
        standing[traced.calls[0]] = "input"
    feeds = traced.feeds(traced.drawn(depth))
    for call, fed_by in feeds.items():
        sources = list(dict.fromkeys(standing[s] for s in fed_by if s in standing))
        layer = layer_for(call.module, call) if call.module is not None else _join(call)
        if layer is None:
            if sources:
                standing[call] = sources[0]
                _band(diagram, sources[0], call)
            continue
        if call.module is not None:
            layer.caption = caption(call)
        diagram.add(layer)
        standing[call] = layer.name
        # The trunk is the source drawn most recently; anything else reaches
        # the layer over the top, the way a residual or a skip is drawn.
        order = {drawn.name: position for position, drawn in enumerate(diagram.layers)}
        trunk = max(sources, key=lambda source: order[source], default="")
        for source in sources:
            style = "forward" if source == trunk else "skip"
            diagram.connect(source, layer.name, style=style)
    return diagram


def _band(diagram: Diagram, source: str, call: Call) -> None:
    """Fold an activation into the convolution that fed it, as its band."""
    layer = diagram[source]
    if _activation(call.module) and type(layer) is Conv:
        banded = ConvRelu(**layer.model_dump(exclude={"kind"}))
        diagram.layers[diagram.layers.index(layer)] = banded
