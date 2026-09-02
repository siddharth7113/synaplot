# Layers

A layer is one drawn element. Every kind takes a `name` and an optional
`caption`. The name must be unique in the diagram, because connections refer to
layers by name, and made of letters, digits, `_` and `-`, because it becomes
part of a TikZ coordinate, where a dot starts an anchor. A name read from a
model, such as `layer1.0.conv1`, needs its dots replaced before it names a
layer; it can still be the caption, through {func}`synaplot.escape`.

## Sizes describe the drawing

`size` says how large to draw the box. It is not the shape of the tensor.

Feature maps are usually drawn shrinking as a network gets deeper, so give a
pooling layer a smaller `height` and `depth` than the convolution before it.
The real shape goes in `filters` and `spatial`, which are written along the
edges of the box:

```yaml
- {kind: conv, name: conv2, filters: 128, spatial: 112,
   size: {width: 3, height: 32, depth: 32}}
```

That draws a box 3 units thick, 32 tall, and 32 deep. The bottom edge is
labelled 128 and the depth edge 112. Sizes are multiplied by the diagram's
`scale`, so at the default scale of 0.2 that box is 6.4 cm deep.

You choose these numbers by eye. Copy them from the closest file in the
[gallery](../gallery.md) and adjust.

`spatial` is free text, so `H/2` works as well as a number. The segmentation
examples use this to label a network whose input size is not fixed.

## Repeated convolutions

`filters` takes a list, and each entry draws its own box. This is how a run of
convolutions is drawn as one layer:

```yaml
- {kind: conv_relu, name: conv3, filters: [256, 256, 256], spatial: 56,
   size: {width: [4, 4, 4], height: 30, depth: 30}}
```

Give `width` a list to draw those boxes at different widths. A single width
applies to all of them, so `width: 4` with three filter counts draws three
boxes 4 units thick.

A filter label wider than its box is rotated 90 degrees, which keeps the labels
of two adjacent boxes from running together into one number. A box with no
neighbour keeps its label upright at any width.

## Every kind of layer

```{synaplot-layers}
```

Write the `kind` in a specification. Import the class from `synaplot` in
Python. Both take the same fields.

## Volumes and flat shapes

The layers fall into two groups, drawn in two different ways.

**Volumes** are 3-D boxes in a row: `conv`, `conv_relu`, `deconv`, `pool`,
`unpool`, `batch_norm`, `fully_connected`, and `softmax`. `sum` and `concat`
are shaded spheres that sit among them. Use these for a convolutional network,
where every layer is a feature map with height, width, and channels.

**Flat shapes** are drawn on the page. `dense` is a column of circles, `block`
is a rounded rectangle holding a line of text, and `operator` is a small circle
holding a symbol. Use these for a plain neural network, a transformer, or a
recurrent cell.

You can mix the two, but a shaded sphere next to flat blocks looks out of
place. `operator` is the flat equivalent of `sum` for that reason.

## Output layers

`softmax` is drawn as a long thin bar. A softmax over classes is a vector with
no spatial extent, and the bar shape says so. The fully connected layers before
it are drawn the same way, so a classifier ends in a row of bars.

Where the output keeps a spatial extent, such as the per-pixel map from a
segmentation network, give it the height and depth of the layer before it:

```yaml
- {kind: softmax, name: out, caption: softmax, classes: 21,
   size: {width: 1, height: 40, depth: 40}}
```

## Overriding a color

Every layer takes a `fill`. It is a TikZ color expression, and it overrides the
[theme](themes.md):

```yaml
- {kind: conv, name: highlight, fill: 'rgb:blue,1.5;red,3.5;green,3.5;white,5'}
```

## Input images

`input` draws an image as a flat plane standing across the depth axis:

```yaml
- {kind: input, name: image, path: cats.jpg, width: 8, height: 8}
```

`width` and `height` are in centimetres, not drawing units, so `scale` does not
apply to them.

The path is read relative to the directory you render from. synaplot copies the
file in beside the LaTeX source, so the same path works inside the temporary
directory the document is compiled in. A missing file raises an error naming
it.
