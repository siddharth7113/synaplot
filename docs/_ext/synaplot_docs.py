"""Sphinx directives that draw synaplot's own diagrams while the docs build.

Every picture in this documentation is rendered from a specification in the
repository when the page that shows it is built, so an example that stops
working stops the build rather than going stale. Reference tables are read off
the code for the same reason.

Two directives are provided:

``synaplot-example``
    Draws one specification and shows the source that drew it.
``synaplot-layers``
    Writes a table of every layer kind a specification can name.
"""

from __future__ import annotations

import runpy
from functools import cache
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar

from docutils import nodes
from docutils.parsers.rst import Directive, directives

import synaplot
from synaplot.core.base import Layer
from synaplot.core.diagram import Diagram
from synaplot.render import ToolchainError
from synaplot.spec import layer_types

if TYPE_CHECKING:
    from sphinx.application import Sphinx

#: The repository, so that a directive can name a file the way a reader would.
ROOT = Path(__file__).resolve().parents[2]

#: Where rendered diagrams are written. Ignored by git; rebuilt on demand.
GALLERY = Path(__file__).resolve().parents[1] / "_gallery"


def load(path: Path) -> Diagram:
    """Return the diagram a file describes.

    Parameters
    ----------
    path
        A specification, or a Python file that builds a diagram.

    Returns
    -------
    Diagram
        The diagram it describes.
    """
    if path.suffix == ".py":
        namespace = runpy.run_path(str(path))
        return next(value for value in namespace.values() if isinstance(value, Diagram))
    from synaplot import spec

    return spec.load(path)


@cache
def library_changed() -> float:
    """Return when synaplot itself was last changed.

    A rendered diagram goes stale when the specification changes and equally
    when the code that draws it changes, so both count.

    Returns
    -------
    float
        The most recent modification time in the package.
    """
    package = Path(synaplot.__file__).parent
    return max(path.stat().st_mtime for path in package.rglob("*") if path.is_file())


def draw(source: Path) -> Path:
    """Render a diagram to SVG, reusing the last render while it is current.

    Parameters
    ----------
    source
        The file describing the diagram.

    Returns
    -------
    Path
        The rendered SVG.
    """
    GALLERY.mkdir(exist_ok=True)
    target = GALLERY / f"{source.stem}.svg"
    if target.exists():
        drawn = target.stat().st_mtime
        if drawn >= source.stat().st_mtime and drawn >= library_changed():
            return target
    return load(source).save(target)


class Example(Directive):
    """Draw one specification and show the source that drew it.

    The argument is a path from the top of the repository, so that the page
    names the file a reader can open.
    """

    required_arguments = 1
    option_spec: ClassVar[dict[str, Any]] = {
        "alt": directives.unchanged,
        "nosource": directives.flag,
    }

    def run(self) -> list[nodes.Node]:
        """Return the picture, and the specification under it."""
        source = ROOT / self.arguments[0]
        if not source.is_file():
            return [self.state.document.reporter.error(f"{source} does not exist")]

        try:
            rendered = draw(source)
        except (ToolchainError, ValueError) as error:
            # A warning rather than an error, so that a build without a LaTeX
            # engine still finishes. The docs build runs with -W, which turns
            # this back into a failure where it matters.
            return [
                self.state.document.reporter.warning(
                    f"{self.arguments[0]} did not render: {error}",
                    line=self.lineno,
                )
            ]

        image = nodes.image(
            uri=f"/_gallery/{rendered.name}",
            alt=self.options.get("alt", f"Diagram drawn by {self.arguments[0]}"),
            classes=["synaplot-example"],
        )
        if "nosource" in self.options:
            return [image]
        listing = nodes.literal_block(
            text=source.read_text(encoding="utf-8"),
            language="yaml" if source.suffix != ".py" else "python",
        )
        listing["caption"] = self.arguments[0]
        return [image, listing]


class Layers(Directive):
    """Write a table of every layer kind a specification can name."""

    def run(self) -> list[nodes.Node]:
        """Return the table."""
        rows = []
        for kind, layer in layer_types().items():
            summary = (layer.__doc__ or "").strip().split("\n")[0]
            # Every layer has a kind, and the first column already gives it.
            own = set(layer.model_fields) - set(Layer.model_fields) - {"kind"}
            fields = sorted(own)
            rows.append((kind, layer.__name__, summary, fields))
        return [
            table(
                ["kind", "Class", "What it draws", "Fields of its own"],
                [
                    [
                        [nodes.literal(text=kind)],
                        [nodes.literal(text=name)],
                        [nodes.Text(summary)],
                        joined(fields),
                    ]
                    for kind, name, summary, fields in rows
                ],
            )
        ]


def joined(names: list[str]) -> list[nodes.Node]:
    """Return field names in code font, separated by commas."""
    cell: list[nodes.Node] = []
    for index, name in enumerate(names):
        if index:
            cell.append(nodes.Text(", "))
        cell.append(nodes.literal(text=name))
    return cell


def table(headers: list[str], rows: list[list[list[nodes.Node]]]) -> nodes.table:
    """Return a table built from inline content.

    Parameters
    ----------
    headers
        One heading per column.
    rows
        Each row, as one list of inline nodes per column.

    Returns
    -------
    docutils.nodes.table
        A table ready to put in a document.
    """
    group = nodes.tgroup(cols=len(headers))
    group += [nodes.colspec(colwidth=1) for _ in headers]
    group += nodes.thead("", row([[nodes.Text(text)] for text in headers]))
    body = nodes.tbody()
    body += [row(cells) for cells in rows]
    group += body
    built = nodes.table()
    built += group
    return built


def row(cells: list[list[nodes.Node]]) -> nodes.row:
    """Return one table row, one cell per list of inline nodes."""
    built = nodes.row()
    for cell in cells:
        entry = nodes.entry()
        entry += nodes.paragraph("", "", *cell)
        built += entry
    return built


def setup(app: Sphinx) -> dict[str, Any]:
    """Register the directives with Sphinx."""
    app.add_directive("synaplot-example", Example)
    app.add_directive("synaplot-layers", Layers)
    return {"parallel_read_safe": True, "parallel_write_safe": True}
