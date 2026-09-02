# API reference

Generated from the code. Every class listed here takes the fields shown, in
Python and in a [specification](../user_guide/specifications.md) alike.

## Diagrams

```{eval-rst}
.. currentmodule:: synaplot

.. autosummary::
   :toctree: generated
   :nosignatures:

   Diagram
   Connection
   Annotation
   Group
   Legend
   LegendEntry
   Theme
```

```{eval-rst}
.. currentmodule:: synaplot.core.theme

.. autosummary::
   :toctree: generated
   :nosignatures:

   Color
```

## Layers

```{eval-rst}
.. currentmodule:: synaplot

.. autosummary::
   :toctree: generated
   :nosignatures:

   Conv
   ConvRelu
   Deconv
   Pool
   Unpool
   BatchNorm
   FullyConnected
   Softmax
   Sum
   Concat
   Input
   Dense
   Block
   Operator
```

## Settings a field takes

These name the choices a field accepts. Every one of them also accepts its
value as a plain string, so `flow="up"` works as well as `flow=Flow.UP`.

```{eval-rst}
.. currentmodule:: synaplot.core.diagram

.. autosummary::
   :toctree: generated
   :nosignatures:

   ConnectionStyle
   Flow
   Bend
   Corner
```

## Shared bases

A layer class inherits from one of these. They take no `kind`, so a
specification cannot name them.

```{eval-rst}
.. currentmodule:: synaplot.layers

.. autosummary::
   :toctree: generated
   :nosignatures:

   BoxLayer
   FilteredBox
   BandedBox
   Resampling
   Ball
```

## Positioning

```{eval-rst}
.. currentmodule:: synaplot

.. autosummary::
   :toctree: generated
   :nosignatures:

   Anchor
   Attach
   Offset
   Size
```

## Base classes

Subclass these to add a layer or a rendering program of your own. See
[writing a layer of your own](../user_guide/custom_layers.md).

```{eval-rst}
.. currentmodule:: synaplot.core.base

.. autosummary::
   :toctree: generated
   :nosignatures:

   Layer
   DrawContext
```

```{eval-rst}
.. currentmodule:: synaplot.render

.. autosummary::
   :toctree: generated
   :nosignatures:

   Tool
   Renderer
   Converter
   Format
   ToolchainError
```

## Reading and writing files

```{eval-rst}
.. currentmodule:: synaplot.spec

.. autosummary::
   :toctree: generated
   :nosignatures:

   load
   loads
   dump
   dumps
   schema
   layer_types
```

## Rendering

```{eval-rst}
.. currentmodule:: synaplot.render

.. autosummary::
   :toctree: generated
   :nosignatures:

   render
   renderers
   converters
   toolchain
```

## Text

```{eval-rst}
.. currentmodule:: synaplot

.. autosummary::
   :toctree: generated
   :nosignatures:

   escape
```
