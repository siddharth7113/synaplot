# Draw your first diagram

This page builds a small convolutional network, renders it, and then does the
same thing from a file instead of from Python. It assumes synaplot and a LaTeX
engine are installed; if `synaplot doctor` reports no engine, see
[installation](install.md).

## Build it in Python

A diagram is layers and the arrows between them. Add layers in drawing order,
and each one that does not say where it goes is placed after the one before it:

```python
import synaplot as sp

diagram = sp.Diagram(name="tiny")
diagram.add(
    sp.ConvRelu(
        name="conv1",
        filters=64,
        spatial=224,
        caption="conv1",
        size=sp.Size(width=2, height=40, depth=40),
    ),
    sp.Pool(name="pool1", size=sp.Size(width=1, height=32, depth=32)),
    sp.ConvRelu(
        name="conv2",
        filters=128,
        spatial=112,
        caption="conv2",
        size=sp.Size(width=3, height=32, depth=32),
    ),
    sp.Softmax(name="out", classes=10, caption="softmax"),
)
for pair in [("conv1", "pool1"), ("pool1", "conv2"), ("conv2", "out")]:
    diagram.connect(*pair)

diagram.save("tiny.svg")
```

The result:

```{synaplot-example} docs/_examples/quickstart.yaml
:alt: A small convolutional network: two convolutions, a pooling layer, and a softmax
:nosource:
```

Three things in that code are worth knowing straight away.

**`size` describes the drawing, not the tensor.** It says how large to draw the
box. Feature maps are usually drawn shrinking as a network gets deeper, so
`pool1` is shorter than `conv1`. The real shape goes in `filters` and
`spatial`, which are written along the edges of the box.

**A list of filters draws one box per entry.** `filters=[64, 64]` draws two
boxes side by side, which is how a run of repeated convolutions is shown as a
single layer. Give `width` a list to draw those boxes different widths;
`vgg16.yaml` in the [gallery](gallery.md) uses this throughout.

**Text is read as LaTeX.** A caption of `$3\times3$` renders as mathematics.
For text you did not write, such as a layer name read from a model, pass it
through {func}`synaplot.escape` first.

## Write it as a file

The same diagram as a specification:

```{literalinclude} _examples/quickstart.yaml
:language: yaml
```

Render it:

```console
synaplot render tiny.yaml -o tiny.svg
```

The format comes from the suffix. Ask for `tiny.png`, `tiny.pdf`, or `tiny.tex`
and you get that instead.

Use a file when the diagram belongs beside the paper it illustrates, or when
another program generates it. Use Python when the diagram comes from a loop or
from a model you already have in memory. Both build the same object, and
`synaplot convert` turns Python into a file.

## Put it in a paper

To get a fragment to paste into a document that already has its own preamble:

```python
print(diagram.to_tex(standalone=False))
```

The output carries the TikZ style definitions it needs, so it compiles
wherever you put it. Every macro it defines is prefixed `\sy@`, so it stays
separate from the commands the surrounding document defines.

## Next

- [Architectures](gallery.md) has a worked file for each common shape of
  network. Copying the closest one is usually faster than starting from nothing.
- The [user guide](user_guide/index.md) covers positioning, the arrow styles,
  themes, and adding a layer of your own.
