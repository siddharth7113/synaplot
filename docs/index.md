# synaplot

Draw neural network architecture diagrams with LaTeX and TikZ.

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

```{toctree}
:maxdepth: 1

install
credits
```
