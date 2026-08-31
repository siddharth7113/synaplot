# Specifications

A diagram can be a YAML or JSON file instead of Python. Both build the same
object, so anything one can express the other can too.

Use a file when the diagram belongs beside the paper it illustrates, or when
another program generates it. Use Python when the diagram comes from a loop or
from a model you already have in memory.

## The shape of a file

```yaml
name: tiny
scale: 0.2
flow: right
layers:
  - {kind: conv, name: conv1, filters: 64, spatial: 224, caption: conv1}
  - {kind: pool, name: pool1, size: {width: 1, height: 32, depth: 32}}
connections:
  - {source: conv1, target: pool1}
annotations:
  - {layer: conv1, text: '$x$', anchor: west, reach: {x: -4}}
legend: {position: south east}
```

Every key has a default, so a file needs only the layers you want drawn. Each
layer needs a `kind`, which names the class that draws it, and a `name`. Its
other keys are the fields of that class, listed in [Layers](layers.md).

JSON is valid YAML, so synaplot reads a `.json` file the same way.

## The commands

```console
synaplot render arch.yaml -o arch.svg
```

`render` also accepts a `.py` file that leaves a `Diagram` in a module-level
variable. If the file builds several, name the one to draw `diagram`.

- `synaplot doctor` lists every rendering program synaplot can use, marks the
  ones it found, says which output formats work, and gives the install command
  for the rest. Run it first when a diagram will not render.
- `synaplot convert arch.py -o arch.yaml` writes a diagram out as a
  specification. Use it to turn Python into YAML, or YAML into JSON.
- `synaplot schema` prints the JSON Schema.

## The schema

`synaplot schema` generates a JSON Schema from the layer classes, covering
every kind and the fields it takes. It cannot drift from what the code accepts.

Use it for two things.

**Editor completion and checking.** Write the schema to a file and point your
editor at it:

```console
synaplot schema -o synaplot.schema.json
```

Most editors then complete `kind` values and mark a misspelled field as you
type.

**Checking generated input.** Validate a specification written by a program or
a model before rendering it. A bad field then produces a message about that
field rather than a LaTeX error.

## What is checked, and when

Loading a file checks the fields. An unknown `kind` and a value of the wrong
type are both rejected. Loading does not check that the layers make a drawing,
because that needs the whole diagram.

Drawing checks the rest. Every connection and annotation must name a layer in
the diagram, and every anchor must be one that layer defines. Both raise a
{class}`ValueError` naming the problem.
