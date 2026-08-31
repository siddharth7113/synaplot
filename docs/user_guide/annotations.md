# Annotations and legends

A connection joins two layers. An annotation joins a layer to a point in the
space around it. Use one to label what reaches a layer without drawing the
layer that supplies it.

## Annotations

```{synaplot-example} examples/softmax_loss.yaml
:alt: A softmax loss layer with four labelled arrows, forward above the axis and gradients below
```

Each annotation names the layer it touches, the anchor on that layer, and how
far the far end of the arrow reaches:

```yaml
- {layer: loss, text: '$p(x^{(t)})$', anchor: west,
   offset: {y: 0.25}, reach: {x: -4}}
```

`offset` shifts the point on the layer. `reach` sets where the other end goes.
Both are in centimetres. `inward` sets the arrow's direction, and defaults to
`true`, which points it at the layer.

The label goes at the far end, on a side taken from the arrow itself:

- An arrow **offset off the layer's axis** has a free side, so its label sits
  on that side and runs back along the arrow. In the preceding figure this puts
  the forward pass above its line and the gradients below theirs. No annotation
  sets a position.
- An arrow **with no offset** has no free side, so its label goes past the end
  of the arrow, clear of the line. The [anchor map](anchors.md) is drawn this
  way.

Text is read as LaTeX, so an annotation can carry mathematics.

## Legends

A legend names each kind of layer in the diagram:

```yaml
legend: {position: south east}
```

In Python:

```python
diagram.add_legend(position="south east")
```

By default the rows come from the layers, one per kind, in drawing order, each
in the color that layer is filled with. Layers that do not stand for a kind of
operation are left out: an input image, and `block`, which carries its own
text.

The legend sits just outside the corner it names, so it covers no part of the
drawing. `position` takes `south east`, `south west`, `north east`, or
`north west`.

To write the rows yourself, set them on the legend:

```python
diagram.legend = sp.Legend(
    position="south west",
    entries=[
        sp.LegendEntry(label="Encoder", role="conv"),
        sp.LegendEntry(label="Decoder", fill="teal"),
    ],
)
```

A row takes its color from `role`, which names a field on the
[theme](themes.md), or from `fill`, which overrides the theme.
