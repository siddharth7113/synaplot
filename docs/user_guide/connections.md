# Connections

A connection is an arrow between two layers. Add one with
{meth}`~synaplot.Diagram.connect` in Python, or as an entry under
`connections:` in a specification:

```yaml
connections:
  - {source: conv1, target: pool1}
```

There are five styles. Which one you want depends on what is in the way.

## forward

A straight arrow from one layer to the next. This is the default.

```{synaplot-example} docs/_examples/connection_forward.yaml
:alt: A straight arrow from a convolution to a pooling layer
:nosource:
```

The faces it runs between come from the diagram's `flow`. In a row it runs from
the source's east face to the target's west face. In an upward stack it runs
from the source's north face to the target's south face. A stack therefore
needs no anchors on any arrow.

## skip

An arrow that leaves the top of the source, runs level above the drawing, and
comes down onto the target.

```{synaplot-example} docs/_examples/connection_skip.yaml
:alt: An arrow leaving the top of the first layer, running above the drawing, and coming down onto the third
:nosource:
```

Use it where a straight arrow would cut through the layers in between. Both
ends rise to the same height, so the run between them is level whatever the two
layers are.

`height` sets the height of that run, as a multiple of the tallest layer's half
height, measured from the diagram's axis. The default of 1.25 puts the run just
above the tallest layer.

## elbow

An arrow that turns one right angle.

```{synaplot-example} docs/_examples/connection_elbow.yaml
:alt: An arrow leaving a layer, turning one right angle, and reaching a smaller layer below and to the right
:nosource:
```

Use it for a branch that leaves the main line, where a straight arrow would
cross the drawing at a long diagonal. `bend` chooses the turn: across and then
down, or down and then across.

## bypass

An arrow that steps out to one side, runs past whatever is in the way, and
comes back in.

```{synaplot-example} docs/_examples/connection_bypass.yaml
:alt: An arrow leaving a block, stepping out to the right, running past a sublayer, and coming back in at a circle
:nosource:
```

This is the shape of a residual path around a sublayer. An elbow cannot draw
one: going around something takes two turns, and an elbow makes one.

`source_anchor` sets the direction it steps out in. A corner steps out to the
side it names, so two bypasses can leave the same layer without overlapping.

`source_anchor: near` or `far` steps out along the depth axis, towards the
reader or away from them. That is where a drawing of feature maps has room, and
it is how several arrows leaving one line reach a row of layers of their own.

`clearance` sets how far to step out. Leave it out for an arrow along the depth
axis and synaplot calculates it: the target's own position fixes the lane, so
the step is the depth between the two layers. HED's five side arrows set no
clearance at all.

## full

A thin line from every unit of one layer to every unit of the next, with no
arrowhead.

```{synaplot-example} docs/_examples/connection_full.yaml
:alt: Two columns of circles, every circle in the first joined to every circle in the second
:nosource:
```

This is how a fully connected layer is drawn. Both ends must be layers drawn as
separate units, which means `dense` at both ends. The lines pass behind the
circles they join.

## Choosing the ends

`source_anchor` and `target_anchor` override the faces a style picks:

```yaml
- {source: enc1, target: enc2, source_anchor: south, target_anchor: north}
```

The U-shaped U-Net uses this to run its encoder down the page while the rest of
the diagram runs across it.

## Arrowheads

An arrow into a flat layer ends in an arrowhead at the anchor. An arrow into a
volume carries its arrowhead partway along the line, because the anchor of a
volume sits at the middle of its depth, inside the shape.
