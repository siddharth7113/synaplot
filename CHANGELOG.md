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
- `Conv`, `ConvRelu`, `Pool`, `Unpool`, `Softmax`, `Sum`, `Concat`, and `Input`.
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
- `Diagram.axis_heights` reports the height each layer is drawn at.
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
- Nine worked examples under `examples/`, carried over from the ones that
  shipped with PlotNeuralNet.

### Changed

- The captions of a row of layers sit on the same line. Each caption used to
  sit under its own layer, which left them at different heights. A drawing with
  a second row of layers below the first gives that row a line of its own.
- A filter label wider than the box it belongs to is turned on its side, so
  that the labels of two boxes drawn side by side read as two numbers rather
  than one. PlotNeuralNet writes `6464` where a layer has 64 filters twice.
- An arrow into a flat layer ends in an arrowhead. An arrow into a layer drawn
  as a volume still carries one partway along, where the box cannot hide it.
- The lines of a `full` connection pass behind the units they join rather than
  across them.
- A `bypass` can leave from a corner as well as a side, so two of them can
  leave the same layer without overlapping.
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
