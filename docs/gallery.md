# Architectures

Each of these is a complete file. Copy the one closest to what you need and
change the numbers; that is usually faster than starting from an empty file.
Every diagram on this page was rendered from the file under it while the page
was built, so what you see is what that file draws.

Render any of them with:

```console
synaplot render examples/vgg16.yaml -o vgg16.svg
```

## LeNet-5

The smallest useful diagram: a row of feature maps, an arrow between each pair,
and a caption under each.

```{synaplot-example} examples/lenet.yaml
:alt: LeNet-5, from a 32 by 32 input through two convolutions and two pooling layers to a softmax over 10 classes
```

The same diagram in Python, which `synaplot render` also accepts:

```{literalinclude} ../examples/lenet.py
:language: python
```

## AlexNet

A plain feed-forward stack, ending in fully connected layers, with a legend
naming each kind of layer.

```{synaplot-example} examples/alexnet.yaml
:alt: AlexNet, five convolutions with pooling, then two fully connected layers and a softmax
```

## VGG16

Repeated convolutions drawn as one layer. `filters` and `width` each take a
list, so one entry in the file draws a block of three convolutions as three
boxes.

```{synaplot-example} examples/vgg16.yaml
:alt: VGG16, five blocks of repeated convolutions separated by pooling layers
```

## Residual block

Normalization layers, and the input added back on at a sphere. The skip runs
over the top, which is where there is room for it.

```{synaplot-example} examples/resnet_block.yaml
:alt: A residual block: two convolutions, each normalized, with the input added back on at the end
```

## U-Net

Skip connections drawn over the top of the network, which is how a wide
encoder and decoder are usually shown in one row.

```{synaplot-example} examples/unet.yaml
:alt: U-Net drawn as one row, with skip connections arching over the top
```

## U-Net, drawn as a U

The same network drawn level by level, the way the original paper shows it.
The encoder steps down the left, the decoder climbs the right, and each level
is joined straight across. Positions are given explicitly, since chaining
cannot make a U.

```{synaplot-example} examples/unet_ushape.yaml
:alt: U-Net drawn as a U, the encoder stepping down the left and the decoder climbing the right
```

## FCN-32s

One prediction, upsampled in a single step by a transposed convolution.

```{synaplot-example} examples/fcn32s.yaml
:alt: FCN-32s, a VGG backbone ending in one prediction upsampled 32 times
```

## FCN-8s

Predictions taken from three depths and summed. Each earlier prediction leaves
the backbone and comes back in at a sphere.

```{synaplot-example} examples/fcn8s.yaml
:alt: FCN-8s, with predictions from three depths summed together before the final upsampling
```

## HED

Five side outputs, one per stage, fanned along the depth axis and fused into a
single edge map. Drawing them in a row below the backbone would run them over
one another; the depth axis is where the room is.

Each side arrow is a `bypass` and none of them says how far to step out. A
bypass along the depth axis works that out from where its target was placed, so
it lands in that lane exactly and the run to the side output is level.

```{synaplot-example} examples/hed.yaml
:alt: HED, a VGG backbone with five side outputs fanned towards the reader and fused into one edge map
```

## Fully connected network

Layers drawn as columns of units rather than as feature maps, joined unit to
unit. Drawing one circle per unit is unreadable for a wide layer, so `nodes`
sets how many circles to draw, and `break_after` marks where the rest were left
out.

```{synaplot-example} examples/mlp.yaml
:alt: A fully connected network drawn as four columns of circles joined unit to unit
```

## Transformer encoder

Flat blocks stacked upward, with each residual path leaving the stack and
added back in at a circle. `flow: up` places each layer above the last and
points every forward arrow the same way, so no layer in the file says where it
goes. A dashed frame marks the block that repeats, and says how many times.

```{synaplot-example} examples/transformer.yaml
:alt: A transformer encoder, flat blocks stacked upward with residual paths added back in at circles
```

## Softmax loss

One layer, annotated with what reaches it and what leaves. The arrows above the
axis carry the forward pass and the ones below carry the gradients.

```{synaplot-example} examples/softmax_loss.yaml
:alt: A softmax loss layer with four labelled arrows, forward above the axis and gradients below
```
