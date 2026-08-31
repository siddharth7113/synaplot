# Credits and provenance

synaplot began as a fork of
[PlotNeuralNet](https://github.com/HarisIqbal88/PlotNeuralNet) by Haris Iqbal,
MIT licensed. The TikZ code that draws every box, banded box, and ball in a
synaplot diagram comes from that project.

Cite both projects if you use synaplot in academic work. PlotNeuralNet's DOI is
[10.5281/zenodo.2526396](https://doi.org/10.5281/zenodo.2526396), and the
repository holds a `CITATION.cff` for synaplot itself.

## What synaplot changed in the styles

The style files live in `src/synaplot/latex/styles/`. Each carries a header
naming its original and listing its changes. The substantive ones:

**Macro namespacing.** The originals stored their TikZ keys in bare macro
names, including `\caption`, `\fill`, `\scale`, `\name`, `\depth`, and
`\opacity`. Loading a style therefore redefined those commands for the rest of
the document. A figure caption in a document that loaded `Box.sty` lost its
`Figure N:` label, and `\fill` is TikZ's own drawing command. Every stored and
computed macro now uses a `\sy@` prefix, and the TikZ style and coordinate
names are prefixed too. Reported upstream as
[HarisIqbal88/PlotNeuralNet#53](https://github.com/HarisIqbal88/PlotNeuralNet/issues/53).

**Depth label placement.** The depth label was drawn at `pos=0`, which put it
at the corner of the box, on top of the width label. On a thin box the two ran
together into a single unreadable number. It is now drawn at `pos=0.5`,
centered on the depth edge. Reported upstream as
[#37](https://github.com/HarisIqbal88/PlotNeuralNet/issues/37),
[#115](https://github.com/HarisIqbal88/PlotNeuralNet/issues/115),
[#122](https://github.com/HarisIqbal88/PlotNeuralNet/issues/122),
[#161](https://github.com/HarisIqbal88/PlotNeuralNet/pull/161),
[#163](https://github.com/HarisIqbal88/PlotNeuralNet/issues/163), and
[#166](https://github.com/HarisIqbal88/PlotNeuralNet/pull/166).

**Style packaging.** The styles were loaded with `\subimport` from a `layers/`
directory reached by a relative path, so a diagram only compiled from the
directory its author happened to use. They now ship inside the package.
Reported upstream as
[#19](https://github.com/HarisIqbal88/PlotNeuralNet/issues/19),
[#65](https://github.com/HarisIqbal88/PlotNeuralNet/issues/65), and
[#146](https://github.com/HarisIqbal88/PlotNeuralNet/issues/146).

**Key naming.** `RightBandedBox` stored its `zlabel` key under a different
macro name than `Box`, so the two pics disagreed. Both now use `\sy@zlabel`.

**Deprecated commands.** `\tikzstyle` is deprecated in pgf and is replaced with
`\tikzset`.

## Relationship to PlotNeuralNet

synaplot does not keep the PlotNeuralNet Python API. The `pycore` functions,
including `to_Conv`, `to_Pool`, and `to_generate`, do not exist here, and
scripts written against them will not run. Only the TikZ styles carry over.
