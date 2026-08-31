# synaplot

Draw neural network architecture diagrams with LaTeX and TikZ.

Describe a network as layers and the arrows between them, in Python or in a
YAML file, and synaplot writes the TikZ and renders it to SVG, PNG, PDF, or
LaTeX source you can paste into a paper.

```{synaplot-example} examples/lenet.yaml
:alt: LeNet-5 drawn as a row of feature maps, from a 32 by 32 input to a softmax over 10 classes
:nosource:
```

That diagram is the following file, rendered while this page was built:

```{literalinclude} ../examples/lenet.yaml
:language: yaml
```

## Where to start

::::{grid} 1 2 2 2
:gutter: 2

:::{grid-item-card} Install
:link: install
:link-type: doc

Get synaplot and a LaTeX engine, and check what you have with
`synaplot doctor`.
:::

:::{grid-item-card} Draw your first diagram
:link: quickstart
:link-type: doc

Ten lines to a rendered network, in Python or YAML.
:::

:::{grid-item-card} Architectures
:link: gallery
:link-type: doc

LeNet, AlexNet, VGG, U-Net, FCN, HED, a residual block, an MLP, and a
transformer encoder, each with the file that drew it.
:::

:::{grid-item-card} User guide
:link: user_guide/index
:link-type: doc

Layers, anchors, connections, themes, and how to add a layer of your own.
:::
::::

## What it gives you

- **One description, four outputs.** The same diagram writes `.svg`, `.png`,
  `.pdf`, and `.tex`.
- **LaTeX you can paste into a paper.** The document carries its own style
  definitions, so it compiles from any directory and needs no files beside
  it.
- **One program instead of a TeX distribution.** Tectonic fetches the LaTeX
  packages a document asks for, so it is the only thing you install.
- **A checkable file format.** Write a diagram as YAML or JSON, and validate
  it against a JSON Schema that `synaplot schema` generates from the code.

synaplot is a rewrite of [PlotNeuralNet](https://github.com/HarisIqbal88/PlotNeuralNet)
by Haris Iqbal. If you have used that project, see
[coming from PlotNeuralNet](from_plotneuralnet.md) for what changed. It is
early, and the API can still change.

```{toctree}
:maxdepth: 1
:hidden:

install
quickstart
gallery
user_guide/index
from_plotneuralnet
api/index
credits
```
