# Writing a layer of your own

synaplot has no registry. It finds layers, renderers, converters, and styles by
walking a base class or reading a directory, so adding one takes a subclass and
nothing else.

## A layer

Subclass {class}`~synaplot.core.base.Layer`, give it a `kind`, and say which
TikZ pic draws it and with what options:

```python
from typing import ClassVar, Literal

from synaplot.core.base import DrawContext, Layer


class Bottleneck(Layer):
    """A bottleneck, drawn as a narrow box."""

    kind: Literal["bottleneck"] = "bottleneck"
    pic: ClassVar[str] = "Box"
    role: ClassVar[str] = "conv"
    title: ClassVar[str] = "Bottleneck"

    channels: int = 64

    def half_height(self, scale: float) -> float:
        return 6 * scale

    def pic_options(self, context: DrawContext) -> dict[str, str]:
        return {
            "fill": self.fill_colour(context, self.role),
            "height": "12",
            "width": "1",
            "depth": "12",
            "xlabel": f'{{{{"{self.channels}",""}}}}',
        }
```

That is enough to use `Bottleneck` in Python. Import the module and it also
works in a specification as `kind: bottleneck`, appears in `synaplot schema`,
and gets a row in a legend.

What each part does:

- **`kind`** is the name a specification writes to ask for this layer. Declare
  it as a `Literal` with a default. synaplot matches a `kind:` in a file to the
  class by that default.
- **`pic`** is the TikZ pic that draws it. The available pics are `Box`,
  `RightBandedBox`, `Ball`, `NodeLayer`, `FlatBlock`, and `FlatOperator`.
- **`role`** names a field on the [theme](themes.md). A layer with no `fill`
  takes its color from there. Leave `role` empty if the theme does not fill the
  layer.
- **`title`** is the name a legend gives the layer. Leave it empty to keep the
  layer out of legends.
- **`half_height`** is how far the layer reaches above its axis. A skip arrow
  is drawn above the tallest layer in the diagram and uses this value to find
  that height. The default is zero, which lets a skip arrow cross your layer.
- **`depth_extent`** is how deep the layer is drawn. Chaining uses it to leave
  room for the diagonal the depth axis is drawn on. The default is zero, which
  suits a flat shape and not a volume.

## The anchors it defines

Override `anchors` if your layer draws fewer coordinates than a box does.
Attaching to an anchor the layer does not define then raises an error listing
the anchors it has:

```python
    @property
    def anchors(self) -> frozenset[Anchor]:
        return Anchor.flat_anchors()
```

`Anchor.ball_anchors`, `Anchor.flat_anchors`, and `Anchor.plane_anchors` cover
the built-in shapes. A layer drawn with the `Box` pic defines every anchor,
which is the default.

## A pic of your own

To draw a shape none of the pics can, write a `.sty` file defining a new pic
and put it in `src/synaplot/latex/styles/`. synaplot reads every file in that
directory into the preamble.

Two rules apply to a style, and tests enforce both.

- **Prefix every macro with `\sy@`.** The styles synaplot inherited stored
  their keys in bare names, including `\caption` and `\fill`, so loading one
  redefined those commands for the rest of the document.
- **Define the coordinates your layer declares.** A test compares each layer's
  `anchors` against the `\coordinate` names its pic writes.

## A rendering program

Adding another LaTeX engine or image converter works the same way. See
[adding another program](../install.md#adding-another-program).
