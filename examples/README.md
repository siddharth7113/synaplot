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
| `fcn32s.yaml` | FCN-32s | A single upsampling step |
| `fcn8s.yaml` | FCN-8s | Predictions from three depths summed together |
| `mlp.yaml` | Fully connected network | Layers drawn as columns of units, joined unit to unit |
| `transformer.yaml` | Transformer encoder | Flat blocks stacked upward, with each residual path added back in at a circle |

These were carried over from the examples that shipped with PlotNeuralNet.

Three of the originals are not here yet:

- `HED` and the U-shaped `U-Net` need arrow routing that synaplot does not have.
  Both branch away from a single line, and every arrow available today is either
  straight or goes over the top of the whole drawing, so both came out as long
  crossing diagonals.
- `SoftmaxLoss` annotates a single box with labelled arrows carrying math, and
  there is no way to draw an annotation yet.
