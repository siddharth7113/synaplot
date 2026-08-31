# Examples

Each file describes one architecture. Render any of them with:

```console
synaplot render examples/vgg16.yaml -o vgg16.svg
```

| File | Architecture | Shows |
| --- | --- | --- |
| `lenet.yaml` | LeNet-5 | The smallest useful diagram |
| `lenet.py` | LeNet-5 | The same diagram built in Python |
| `alexnet.yaml` | AlexNet | A plain feed-forward stack |
| `vgg16.yaml` | VGG16 | Repeated convolutions drawn as one layer |
| `unet.yaml` | U-Net | Skip connections over the top |
| `unet_ushape.yaml` | U-Net | The U layout of the paper, using explicit positions and concatenations |
| `fcn32s.yaml` | FCN-32s | A single upsampling step |
| `fcn8s.yaml` | FCN-8s | Predictions from three depths summed together |
| `hed.yaml` | HED | Side outputs branching off a backbone |

These were carried over from the examples that shipped with PlotNeuralNet.

`SoftmaxLoss` has not been carried over. It annotates a single box with labelled
forward and backward arrows carrying math, and synaplot has no way to draw an
annotation yet.
