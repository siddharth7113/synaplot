# Examples

Each file describes one architecture. Render any of them with:

```console
synaplot render examples/vgg16.yaml -o vgg16.svg
```

| File | Architecture | Shows |
| --- | --- | --- |
| `lenet.yaml` | LeNet-5 | The smallest useful diagram |
| `lenet.py` | LeNet-5 | The same diagram built in Python |
| `alexnet.yaml` | AlexNet | A plain feed-forward stack, with a legend |
| `vgg16.yaml` | VGG16 | Repeated convolutions drawn as one layer |
| `resnet_block.yaml` | Residual block | Normalization layers, and the input added back on |
| `unet.yaml` | U-Net | Skip connections over the top |
| `unet_ushape.yaml` | U-Net | The same network drawn as a U, level by level |
| `fcn32s.yaml` | FCN-32s | A single upsampling step |
| `fcn8s.yaml` | FCN-8s | Predictions from three depths summed together |
| `hed.yaml` | HED | Side outputs fanned along the depth axis |
| `softmax_loss.yaml` | Softmax loss | One layer, annotated with what goes in and comes out |
| `mlp.yaml` | Fully connected network | Layers drawn as columns of units, joined unit to unit |
| `transformer.yaml` | Transformer encoder | Flat blocks stacked upward, each residual path added back in at a circle, and a frame around the block that repeats |

These were carried over from the examples that shipped with PlotNeuralNet.
