# Diagrams

A {class}`~synaplot.Diagram` holds layers, the connections between them, and
the settings for the whole drawing. Layers are drawn in the order you add them.

## Chaining

A layer that does not say where it goes is placed after the one before it. A
feed-forward network therefore needs no positioning:

```python
diagram = sp.Diagram(name="chain")
diagram.add(sp.Conv(name="conv1"), sp.Pool(name="pool1"), sp.Conv(name="conv2"))
```

The space between two chained layers is calculated from how deep each one is
drawn. TikZ draws the depth axis on a diagonal, so a deep layer reaches further
across the page than its width accounts for. Set `margin` to change the extra
space, or `gap` to space every pair equally and ignore depth:

```python
sp.Diagram(name="even", gap=1.6)
```

## Two kinds of measurement

Diagrams use two units, and mixing them up is the most common source of
surprise.

**Sizes are multiplied by `scale`.** A `Size` of `height=40` at the default
scale of 0.2 draws a box 8 cm tall.

**Positions are in centimetres.** `gap`, `margin`, every `Offset` on a layer or
an annotation, and a connection's `clearance` are page distances. `scale` does
not apply to them.

So changing `scale` grows every layer, but leaves any position you wrote by
hand where it was. A diagram built only by chaining scales as a whole. A
diagram with explicit offsets, such as the U-shaped U-Net, needs those offsets
adjusted as well:

```python
sp.Diagram(name="big", scale=0.4)
```

To make a finished image larger without changing the drawing, raise `dpi` when
saving a PNG, or save an SVG and set its display size.

## Which way a chain runs

`flow` sets the direction of chaining, and forward arrows follow it.

- `right` is the default. Each layer is placed to the right of the last, which
  is how a row of feature maps is drawn. A forward arrow runs from a layer's
  east face to the next layer's west face.
- `up` places each layer above the last, which is how the parts of a
  transformer or a recurrent cell are drawn. A forward arrow runs from a
  layer's north face to the next layer's south face.

```python
sp.Diagram(name="encoder", flow="up")
```

Because the flow chooses the faces, a stack needs no anchors on any arrow. The
transformer encoder in the [gallery](../gallery.md) is 24 lines, and no layer
in it says where it goes.

## Captions

A caption is drawn under its layer. Layers whose axes coincide form a row, and
the captions of a row sit on one line. That line hangs from the lowest point
any layer in the row reached, measured from the finished drawing, so a row of
shrinking feature maps still gets a straight line of captions.

A second row of layers gets a line of its own. Depth counts as well as height:
a layer set towards the reader is drawn lower on the page, so it forms its own
row. In HED that keeps the five side outputs out of the backbone's row.

## Saving

The format comes from the suffix:

```python
diagram.save("net.svg")
diagram.save("net.png", dpi=300)
diagram.save("net.pdf")
diagram.save("net.tex")
```

Compiling happens in a temporary directory, and only the file you asked for is
copied out.

To get LaTeX source rather than a file, call {meth}`~synaplot.Diagram.to_tex`.
The document carries the TikZ style definitions it needs, so it compiles from
any directory. A diagram that draws no input image is a single self-contained
file, which you can upload to Overleaf on its own.

Pass `standalone=False` for a fragment to paste into a document that has its
own preamble. Every macro the styles define is prefixed `\sy@`, so it stays
separate from the commands the surrounding document defines.
