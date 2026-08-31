# Themes

A {class}`~synaplot.Theme` holds the color for each kind of layer. Every value
is a TikZ color expression. It can name a color, such as `teal`, or mix
several, such as `rgb:blue,5;green,15`.

## Using a different theme

Copy the default and override the roles you want to change:

```python
mono = sp.Theme(name="mono", conv="gray!30", pool="gray!60", softmax="black!70")
diagram = sp.Diagram(name="net", theme=mono)
```

In a specification, list only the roles you are changing:

```yaml
theme:
  name: mono
  conv: gray!30
  pool: gray!60
```

## What each role colors

Most roles are named after the layer they fill: `conv`, `deconv`, `pool`,
`unpool`, `fc`, `softmax`, `sum`, `concat`, and `batchnorm`.

Two are not. `conv_band` and `fc_band` color the band down the right of a
convolution or a fully connected layer, which stands for the activation after
it. The layer itself is filled with `conv` or `fc`, so these two color part of
a layer.

`edge` colors every arrow.

## Changing one layer

To change a single layer rather than every layer of its kind, set `fill` on
that layer. It overrides the theme:

```yaml
- {kind: conv, name: highlight, fill: 'rgb:blue,1.5;red,3.5;green,3.5;white,5'}
```

## How a color reaches the drawing

Each role becomes a LaTeX macro in the preamble, named after the role. `conv`
becomes `\syColorConv`, and `conv_band` becomes `\syColorConvBand`. A layer
with no `fill` of its own refers to the macro, so one theme change moves every
layer that uses it, and the LaTeX stays readable.
