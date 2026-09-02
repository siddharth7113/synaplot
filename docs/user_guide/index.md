# User guide

These pages explain the parts of a diagram in the order you meet them. If you
have not drawn anything yet, start with
[Draw your first diagram](../quickstart.md).

```{toctree}
:maxdepth: 1

diagrams
layers
anchors
connections
annotations
themes
specifications
custom_layers
```

- **[Diagrams](diagrams.md)**: how layers are placed, which way a chain runs,
  what the units are, and how a diagram is saved.
- **[Layers](layers.md)**: every kind of layer, and why `size` describes the
  drawing rather than the tensor.
- **[Anchors](anchors.md)**: how to position a layer by attaching it to a
  named point on another layer.
- **[Connections](connections.md)**: the five arrow styles, and when each one
  is the right shape.
- **[Annotations, legends, and groups](annotations.md)**: the text around a
  drawing, and frames around parts of it.
- **[Themes](themes.md)**: colors.
- **[Specifications](specifications.md)**: the file format, the command line,
  and the JSON Schema.
- **[Writing a layer of your own](custom_layers.md)**: how to extend synaplot.
