"""A small convolutional network, drawn with a skip connection.

Render it with::

    synaplot render examples/lenet.py -o lenet.svg
"""

import synaplot as sp

diagram = sp.Diagram(name="lenet")
diagram.add(
    sp.Conv(name="conv1", filters=64, spatial=512, caption="conv1"),
    sp.Pool(name="pool1"),
    sp.ConvRelu(
        name="conv2",
        filters=[128, 128, 128],
        spatial=256,
        size=sp.Size(width=[3, 3, 3], height=30, depth=30),
        caption="conv2",
    ),
    sp.Pool(name="pool2", size=sp.Size(width=1, height=24, depth=24)),
    sp.Softmax(name="out", classes=10, caption="softmax"),
)
diagram.connect("conv1", "pool1")
diagram.connect("pool1", "conv2")
diagram.connect("conv2", "pool2")
diagram.connect("pool2", "out")
diagram.connect("conv1", "out", style="skip")
