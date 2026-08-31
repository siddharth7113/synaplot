# Changelog

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and
this project uses [semantic versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

synaplot is a rewrite of PlotNeuralNet with a new API. PlotNeuralNet scripts do
not run against it.

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

### Changed

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
  horizontal room that its width does not account for, and a fixed distance
  left neighbouring layers overlapping. Set `gap` to space every pair
  equally.
- Rendering runs in a temporary directory and copies out only the file you
  asked for. `tikzmake.sh` deleted every `.tex` file in the working directory.

### Removed

- `pycore`, `pyexamples`, and `tikzmake.sh`.
