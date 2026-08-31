# synaplot

Draw neural network architecture diagrams with LaTeX and TikZ.

You describe a network as a list of layers and the connections between them.
synaplot turns that into TikZ code and renders it to SVG, PNG, PDF, or LaTeX
source.

synaplot is a rewrite of [PlotNeuralNet](https://github.com/HarisIqbal88/PlotNeuralNet)
as a Python package. It is early, and the API will change.

```python
import synaplot as sp

diagram = sp.Diagram(name="lenet")
diagram.add(
    sp.Conv(name="conv1", filters=64, spatial=512, caption="conv1"),
    sp.Pool(name="pool1"),
    sp.Softmax(name="out", classes=10, caption="softmax"),
)
diagram.connect("conv1", "pool1")
diagram.connect("pool1", "out")
diagram.save("lenet.svg")
```

The same diagram from the command line:

```console
synaplot render examples/lenet.py -o lenet.svg
```

## Installing

```console
pip install synaplot
```

Writing LaTeX source needs nothing else. A PDF or an image needs a LaTeX
engine, and an SVG or PNG needs a converter too. To see what you have and how
to install the rest:

```console
synaplot doctor
```

[tectonic](https://tectonic-typesetting.github.io/) is the shortest route,
since it is one program that downloads the LaTeX packages a document asks for
rather than needing a TeX installation.

## Credits

The TikZ code that draws these diagrams comes from PlotNeuralNet by Haris Iqbal,
MIT licensed. synaplot ships it in
[src/synaplot/latex/styles/](src/synaplot/latex/styles/), and each file records
what changed.

Cite both projects if you use synaplot in academic work. See
[CITATION.cff](CITATION.cff). PlotNeuralNet's DOI is
[10.5281/zenodo.2526396](https://doi.org/10.5281/zenodo.2526396).

## License

MIT. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
