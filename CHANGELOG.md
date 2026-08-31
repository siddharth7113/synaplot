# Changelog

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and
this project uses [semantic versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

synaplot is a rewrite of PlotNeuralNet with a new API. Scripts written for
PlotNeuralNet do not work with synaplot.

### Added

- Python packaging: hatchling and a src layout.
- TikZ styles ship with the package.
- `Diagram`, with layers and the connections between them. A layer that does
  not say where it goes is placed after the one before it.
- `Conv`, `ConvRelu`, `Deconv`, `Pool`, `Unpool`, `FullyConnected`,
  `BatchNorm`, `Softmax`, `Sum`, `Concat`, and `Input`. PlotNeuralNet defined
  colours for a fully connected layer, a deconvolution and a normalization
  layer and then never drew any of them.
- `Diagram.to_tex` writes a document that carries its own styles, so it
  compiles from any directory and pastes into Overleaf as is.
- `Diagram.save` writes `.tex`, `.pdf`, `.svg`, or `.png`, picking the format
  from the suffix.
- Rendering through tectonic, lualatex, xelatex, or pdflatex, and conversion
  through dvisvgm or pdftocairo. The installed program with the lowest priority
  is used. Subclass `Renderer` or `Converter` to add another.
- `synaplot render` and `synaplot doctor`. `doctor` reports which programs are
  installed, which formats work, and how to install what is missing.
- `escape`, for text that did not come from you.
- A diagram can be written as YAML or JSON and read back. `synaplot render`
  accepts a `.yaml` or `.json` file as well as a `.py` one.
- `synaplot schema` prints a JSON Schema covering every layer kind, for editor
  completion or for checking a specification a program generated.
- `synaplot convert` writes a diagram out as a specification, so a Python file
  can become YAML.
- `Diagram.axes` reports the height and the depth each layer is drawn at.
- `Diagram.flow` sets which way a chain of layers runs. `up` stacks each layer
  above the one before it and points every forward arrow the same way, so a
  transformer needs no positioning and no anchors. `right` is the default and
  is how a row of feature maps is drawn.
- An `Offset` field can hold a TikZ expression instead of a number, for a
  distance only the drawing knows.
- Flat shapes, for architectures that are not stacks of feature maps. `Dense`
  draws a layer as a column of units, the way a plain neural network is shown,
  and `Block` draws a rounded box holding a line of text, the way the parts of
  a transformer or a recurrent cell are shown. `Operator` draws a small circle
  holding a symbol, for the point where a residual path is added back.
- Three more connection styles. `full` joins every unit of one layer to every
  unit of the next. `elbow` turns one right angle, for a branch leaving the
  main line. `bypass` steps out to one side, runs past whatever is in the way,
  and comes back in, which is the shape of a residual connection.
- A `fill` on any layer, overriding the colour the theme would give it.
- `Diagram.annotate` draws a labelled arrow beside a layer, between it and a
  point in the space around it, for saying what reaches a layer and what leaves
  it without drawing the layer that supplies it. The label hugs the arrow, so
  two arrows into one face read as two.
- `Diagram.add_legend` draws a key in a corner of the drawing, naming each kind
  of layer the diagram draws and the colour it is drawn in. It sits just clear
  of the corner it names, so it covers nothing. List the entries yourself to
  say something else.
- Thirteen worked examples under `examples/`, carried over from the ones that
  shipped with PlotNeuralNet. `hed.yaml`, `unet_ushape.yaml` and
  `softmax_loss.yaml` are the three that needed drawing synaplot could not do
  until now; `resnet_block.yaml` is new.

### Changed

- An input image works. It was drawn as a plain TikZ node, while every other
  layer is addressed as `name-anchor`, so chaining a layer after an image or
  drawing an arrow from one failed to compile. The image is also copied in
  beside the LaTeX source, so a path written relative to the directory you
  render from resolves inside the temporary directory the document is compiled
  in, and it is reflected once, because the depth axis runs to the lower left
  and left the picture mirrored.
- Attaching to an anchor a layer does not define is refused, and says which
  anchors that layer has. A ball has no corners and a flat shape has no depth,
  and LaTeX reports the mistake as `No shape named ... is known`, several
  hundred lines into its own log. Naming a layer that is not in the diagram is
  refused the same way, which a specification could do silently.
- The theme's band colours are `conv_band` and `fc_band`, not `conv_relu` and
  `fc_relu`. They colour the band down the right of a layer, which stands for
  the activation; the layer itself is filled with `conv` or `fc`. The old names
  described a kind of layer while colouring part of one.
- A transposed convolution has a colour of its own. It shared one with
  upsampling, so a drawing could not tell the two apart.
- `Diagram.scale` is a number. It was a model wrapping one number, so setting
  it read `Diagram(scale=Scale(value=0.4))`.
- `Diagram.save` takes `fmt` and `renderer`, which only `render` accepted.
- The diagram's `scale` reaches the layers it draws. Layers used to be spaced
  for the scale set and drawn at the default one, so any scale but the default
  lined up nothing.
- The captions of a row of layers sit on the same line, read off the lowest
  point any layer of that row drew. Each caption used to sit under its own
  layer, which left them at different heights. A drawing with a second row of
  layers below the first gives that row a line of its own. Depth counts as
  well as height, because TikZ draws the depth axis diagonally: a layer set
  towards the reader is drawn lower on the page than the row it was chained
  from, and its caption goes with it.
- `\syCaptionDrop` and `\syCaptionWidth` set how far below a row its captions
  sit and how wide they set. A pic no longer draws its own caption, so the
  `caption` key is gone from `Box`, `RightBandedBox`, `Ball`, `NodeLayer`, and
  `FlatBlock`.
- How far across the page a unit of depth reaches is read off the picture's own
  z axis. It used to be written into the Python as 0.385, which is TikZ's
  default and was wrong for any document that set a different one.
- A filter label wider than the box it belongs to is turned on its side, so
  that the labels of two boxes drawn side by side read as two numbers rather
  than one. PlotNeuralNet writes `6464` where a layer has 64 filters twice.
- An arrow into a flat layer ends in an arrowhead. An arrow into a layer drawn
  as a volume still carries one partway along, where the box cannot hide it.
- The lines of a `full` connection pass behind the units they join rather than
  across them.
- A `bypass` can leave from a corner as well as a side, so two of them can
  leave the same layer without overlapping. It can also step out along the
  depth axis, towards the reader or away from them, which is how several arrows
  leaving one line reach a row of layers of their own. One that steps along the
  depth axis works out how far to step from where its target was placed, so
  five such arrows land in five lanes without a distance written on any of
  them.
- `Dense` leaves a gap at its break and draws the ellipsis to scale with its
  circles. The ellipsis used to be text at document size in a gap too small
  for it.
- Style macros use a private `\sy@` namespace. Loading a style no longer
  overwrites `\caption`, `\fill`, `\scale`, `\name`, `\depth`, or `\opacity`.
- The depth label is centered on the depth edge instead of the corner.
- `RightBandedBox` and `Box` read the same `zlabel` key.
- A convolution draws every filter it is given. PlotNeuralNet drew the first
  two and dropped the rest.
- Both ends of a skip connection rise to the same height, so the arrow between
  them is level.
- Layers are spaced by how deep they are drawn rather than by a fixed
  distance. TikZ draws the depth axis on a diagonal, so a deep layer takes up
  horizontal room that its width does not account for. At a fixed distance,
  two deep layers overlapped. Set `gap` to space every pair equally instead.
- Rendering runs in a temporary directory and copies out only the file you
  asked for. `tikzmake.sh` deleted every `.tex` file in the working directory.

### Removed

- `pycore`, `pyexamples`, and `tikzmake.sh`.
