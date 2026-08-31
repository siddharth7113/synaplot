# Changelog

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and
this project uses [semantic versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

synaplot is a rewrite of PlotNeuralNet with a new API. PlotNeuralNet scripts do
not run against it.

### Added

- Python packaging: hatchling, a src layout, and a `synaplot` command.
- TikZ styles ship with the package.

### Changed

- Style macros use a private `\sy@` namespace. Loading a style no longer
  overwrites `\caption`, `\fill`, `\scale`, `\name`, `\depth`, or `\opacity`.
- The depth label is centered on the depth edge instead of the corner.
- `RightBandedBox` and `Box` read the same `zlabel` key.

### Removed

- `pycore`, `pyexamples`, and `tikzmake.sh`.
