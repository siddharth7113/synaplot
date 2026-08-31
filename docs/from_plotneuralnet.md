# Coming from PlotNeuralNet

synaplot is a rewrite of [PlotNeuralNet](https://github.com/HarisIqbal88/PlotNeuralNet).
It draws with the same TikZ pics, so diagrams look familiar, but with a new python layer on top, scripts written for PlotNeuralNet are not compatible

This page maps one onto the other. For the licence and the list of changes to
the style files, see [credits and provenance](credits.md).

## What replaced each function

PlotNeuralNet builds a list of strings and writes them to a `.tex` file.
synaplot builds a `Diagram` object and renders it.

| PlotNeuralNet | synaplot |
| --- | --- |
| `to_head`, `to_cor`, `to_begin`, `to_end` | Nothing. `Diagram.to_tex` writes the whole document, styles included. |
| `to_generate(arch, "file.tex")` | `diagram.save("file.tex")`, or `.svg`, `.png`, `.pdf` |
| `to_Conv` | `Conv` |
| `to_ConvConvRelu` | `ConvRelu` with a list of filters |
| `to_ConvRes` | `ConvRelu` with a grey `fill` and a low `opacity` |
| `to_Pool`, `to_UnPool` | `Pool`, `Unpool` |
| `to_SoftMax`, `to_ConvSoftMax` | `Softmax` |
| `to_Sum` | `Sum`, or `Operator` beside flat shapes |
| `to_input` | `Input` |
| `to_connection` | `Diagram.connect(source, target)` |
| `to_skip` | `Diagram.connect(source, target, style="skip")` |
| `block_2ConvPool`, `block_Unconv`, `block_Res` | No equivalent. Write the layers out, or build them in a loop. |
| `tikzmake.sh` | `synaplot render`. Nothing is deleted by glob. |

Layers PlotNeuralNet had no function for: `FullyConnected`, `BatchNorm`,
`Deconv`, `Dense`, `Block`, `Operator`, and `Concat`. It defined `\FcColor` and
`\FcReluColor` in 2018 and never drew a layer with either.

## What changed in the output

Your diagram will not come out pixel for pixel the same. We have made the following fixes:

- **Depth labels no longer collide.** The label along the depth edge was drawn
  at the corner, on top of the label along the bottom edge, so a layer with 64
  filters and 512 pixels read as `64512`. It is centred on its edge now.
- **A run of convolutions draws every filter.** `to_ConvConvRelu` read the
  first two entries of its filter list and dropped the rest.
- **A wide filter label turns on its side** rather than running into its
  neighbour's. Two boxes with 64 filters each read as `6464` before.
- **Captions in a row line up.** Each caption used to sit under its own layer,
  which left a shrinking stack of feature maps with captions at as many
  different heights.
- **Layers are spaced by how deep they are drawn.** TikZ draws the depth axis
  on a diagonal, so a deep layer reaches further across the page than its width
  accounts for. At a fixed distance, two deep layers overlapped.
- **Skip arrows run level.** Both ends rise to the same height, so a skip
  between two layers of different heights is no longer a slope.
- **The mesh of a fully connected layer passes behind its units** rather than
  across them.

## What is safe about the LaTeX now

Three problems made PlotNeuralNet's output awkward to put in a paper.

**Macros no longer leak.** The styles stored their TikZ keys in bare macro
names, including `\caption`, `\fill`, `\scale`, `\name`, `\depth`, and
`\opacity`. Loading one redefined those commands for the rest of the document,
so a figure caption in the same document lost its `Figure N:` label, and
`\fill` is TikZ's own drawing command. Every macro is now prefixed `\sy@`, and
`to_tex(standalone=False)` is safe to paste into a real paper.

**The document carries its own style definitions.** PlotNeuralNet used
`\subimport` to pull in a `layers/` directory, so its output compiled only from
the directory it was generated in, and needed that directory alongside it
anywhere else. synaplot writes the definitions into the preamble instead.

**Nothing is deleted.** `tikzmake.sh` ran `rm *.tex` against the whole working
directory. Rendering happens in a temporary directory and only the file you
asked for is copied out.

## What synaplot does not carry over

- **The block helpers.** `block_2ConvPool` and the others were shortcuts for a
  few architectures. Write the layers out, or build them in a Python loop.
- **`to_head` and the path juggling.** There is no project path to pass around,
  because there are no external style files to find.

## What is new

- A file format. A diagram can be YAML or JSON, and `synaplot schema`
  generates a JSON Schema to check it against.
- SVG and PNG output, and a `doctor` command that says what is installed and
  how to install the rest.
- Flat shapes, so a plain neural network, a transformer, or a recurrent cell
  can be drawn as well as a stack of feature maps.
- Three more arrow styles: `elbow`, `bypass`, and `full`.
- Annotations and legends.
- Themes, and a `fill` on any single layer.
