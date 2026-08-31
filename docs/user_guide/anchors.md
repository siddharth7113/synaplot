# Anchors

By default each layer is placed after the one before it. To put a layer
anywhere else, attach it to a named point on another layer. That point is an
anchor.

## The map

Every layer defines named coordinates on itself. A box defines the most:

```{synaplot-example} docs/_examples/anchors.yaml
:alt: A box with arrows pointing at its north, south, east, west, near, far, nearnortheast, and farsouthwest anchors
:nosource:
```

A name reads outwards from the depth axis. `nearnortheast` is the corner
towards the reader, at the top, on the right. `near` faces the reader, and
`far` faces away.

Two details in that picture matter later. `east` and `west` sit at the middle
of the box's depth, not on the visible front edge, so an arrowhead placed there
falls inside the shape. A `far` anchor is behind the box, so an arrow reaching
one passes through it.

## Attaching a layer

In a specification, `to` says where a layer goes:

```yaml
- {kind: conv, name: side, filters: 1,
   to: {layer: conv5, anchor: east, offset: {x: 3, z: 8}}}
```

In Python:

```python
sp.Conv(
    name="side",
    filters=1,
    to=sp.Attach(layer="conv5", anchor="east", offset=sp.Offset(x=3, z=8)),
)
```

synaplot places the layer at that anchor, then shifts it by `offset`. Offsets
are in centimetres on the page. The diagram's `scale` does not apply to them.

Attach to a face for a layer that continues from another. Attach to a corner to
line two layers up. Attaching to `southwest` rather than `south` puts the new
layer's west edge on the old layer's west edge, and that is how the levels of
the U-shaped U-Net line up.

## Not every layer has every anchor

A sphere has no corners, and a flat shape has no depth. Attaching to an anchor
a layer does not define raises an error listing the anchors it does have:

```text
the arrow from 'c' to 'add1' reaches 'add1' at its northeast, which it does not
define. 'add1' defines: anchor, east, north, south, west.
```

LaTeX reports the same mistake as `No shape named 'add1-northeast' is known`,
several hundred lines into its log, so synaplot checks first.

## Offsets the drawing calculates

An offset is usually a number. It can also be a TikZ expression, for a distance
the drawing fixes rather than you:

```python
sp.Offset(x=r"8*\syDepthSlant+1")
```

`\syDepthSlant` is how far across the page one unit of depth reaches. It is
read from the picture's own z axis, so it stays correct in a document that
changes that axis. Chaining uses it to leave room for two deep layers.

An expression has no value until the drawing exists, so synaplot cannot use it
to work out which row a layer is in. Give `y` and `z` as numbers.
