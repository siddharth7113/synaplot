"""LeNet-5, built in Python.

This is the diagram ``lenet.yaml`` describes, written with the Python API
instead. A test holds the two to drawing the same thing.

Render it with::

    synaplot render examples/lenet.py -o lenet.svg
"""

import synaplot as sp

diagram = sp.Diagram(name="lenet")
diagram.add(
    sp.Conv(
        name="conv1",
        filters=6,
        spatial=28,
        caption="conv1",
        size=sp.Size(width=2, height=40, depth=40),
    ),
    sp.Pool(name="pool1", size=sp.Size(width=1, height=32, depth=32)),
    sp.Conv(
        name="conv2",
        filters=16,
        spatial=10,
        caption="conv2",
        size=sp.Size(width=3, height=32, depth=32),
    ),
    sp.Pool(name="pool2", size=sp.Size(width=1, height=20, depth=20)),
    sp.FullyConnected(
        name="fc1", units=120, caption="fc1", size=sp.Size(width=3, height=3, depth=25)
    ),
    sp.FullyConnected(
        name="fc2", units=84, caption="fc2", size=sp.Size(width=3, height=3, depth=25)
    ),
    sp.Softmax(name="out", classes=10, caption="softmax"),
)
for source, target in [
    ("conv1", "pool1"),
    ("pool1", "conv2"),
    ("conv2", "pool2"),
    ("pool2", "fc1"),
    ("fc1", "fc2"),
    ("fc2", "out"),
]:
    diagram.connect(source, target)
