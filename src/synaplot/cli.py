"""The synaplot command."""

from __future__ import annotations

import json
import platform
import runpy
import sys
from pathlib import Path
from typing import Annotated

import typer
import yaml

from synaplot import __version__, spec
from synaplot.core.diagram import Diagram
from synaplot.render import Format, ToolchainError, converters, renderers, toolchain

SPEC_SUFFIXES = {".yaml", ".yml", ".json"}

app = typer.Typer(
    name="synaplot",
    help="Draw neural network architecture diagrams with LaTeX and TikZ.",
    no_args_is_help=True,
    add_completion=False,
)


def _fail(message: str) -> None:
    """Print a message to standard error and stop with a non-zero status."""
    typer.secho(message, fg=typer.colors.RED, err=True)
    raise typer.Exit(code=1)


def _load(source: Path) -> Diagram:
    """Return the diagram a file describes.

    A YAML or JSON file is read as a specification. A Python file is run, and
    the ``Diagram`` it leaves in a module-level variable is returned. A Python
    file that builds several must name the one to draw ``diagram``.

    Parameters
    ----------
    source
        The file to read.

    Returns
    -------
    Diagram
        The diagram the file describes.
    """
    if not source.is_file():
        _fail(f"{source} does not exist")

    if source.suffix.lower() in SPEC_SUFFIXES:
        try:
            return spec.load(source)
        except (ValueError, TypeError, yaml.YAMLError) as error:
            _fail(f"{source}: {error}")

    sys.path.insert(0, str(source.parent.resolve()))
    try:
        namespace = runpy.run_path(str(source))
    except Exception as error:
        _fail(f"{source} raised {type(error).__name__}: {error}")
    finally:
        sys.path.pop(0)

    found = {
        name: value
        for name, value in namespace.items()
        if isinstance(value, Diagram) and not name.startswith("_")
    }
    if not found:
        _fail(f"{source} does not leave a Diagram in a module-level variable")
    if len(found) > 1 and "diagram" not in found:
        names = ", ".join(sorted(found))
        _fail(f"{source} builds several diagrams ({names}); name one of them 'diagram'")
    return found.get("diagram") or next(iter(found.values()))


@app.command()
def render(
    source: Annotated[
        Path,
        typer.Argument(help="A .yaml, .json, or .py file describing a diagram."),
    ],
    output: Annotated[
        Path,
        typer.Option("--output", "-o", help="Where to write the diagram."),
    ],
    dpi: Annotated[int, typer.Option(help="Resolution for PNG output.")] = 300,
) -> None:
    """Draw a diagram and write it to a file.

    The format comes from the suffix of the output file: .tex, .pdf, .svg,
    or .png.
    """
    diagram = _load(source)
    try:
        written = diagram.save(output, dpi=dpi)
    except (ToolchainError, ValueError) as error:
        _fail(str(error))
    typer.secho(f"wrote {written}", fg=typer.colors.GREEN)


@app.command()
def doctor() -> None:
    """Report which rendering programs are installed.

    Run this first when a diagram will not render. Every program synaplot can
    use is listed, along with how to install the missing ones.
    """
    typer.echo(f"synaplot {__version__} on {platform.system()} {platform.machine()}")
    typer.echo(f"python {platform.python_version()}\n")

    width = max(len(cls.name) for cls, _ in toolchain())
    for cls, found in toolchain():
        mark, color = (
            ("found", typer.colors.GREEN) if found else ("-", typer.colors.YELLOW)
        )
        typer.echo(f"  {cls.name:<{width}}  ", nl=False)
        typer.secho(f"{mark:<7}", fg=color, nl=False)
        typer.echo("" if found else f" to install, {cls.install_hint()}")

    typer.echo("")
    can_compile = bool(renderers())
    for fmt in Format:
        if fmt is Format.TEX:
            ready = True
        elif fmt is Format.PDF:
            ready = can_compile
        else:
            ready = can_compile and bool(converters(fmt))
        mark, color = ("yes", typer.colors.GREEN) if ready else ("no", typer.colors.RED)
        typer.echo(f"  {fmt.value:<4} ", nl=False)
        typer.secho(mark, fg=color)

    if not can_compile:
        typer.secho(
            "\nNo LaTeX engine was found, so only .tex output works. "
            "Installing tectonic is the shortest route: it needs no TeX "
            "installation and downloads what a document asks for.",
            fg=typer.colors.YELLOW,
        )


@app.command()
def convert(
    source: Annotated[Path, typer.Argument(help="The diagram to read.")],
    output: Annotated[
        Path,
        typer.Option("--output", "-o", help="Where to write the specification."),
    ],
) -> None:
    """Write a diagram out as a specification.

    Use it to turn a Python file into a .yaml or .json specification, or to
    convert between the two.
    """
    diagram = _load(source)
    written = spec.dump(diagram, output)
    typer.secho(f"wrote {written}", fg=typer.colors.GREEN)


@app.command()
def schema(
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="Write to a file instead of stdout."),
    ] = None,
) -> None:
    """Print the JSON Schema for a specification.

    Point an editor at it to get completion and checking while writing a
    specification by hand, or give it to a program that generates one.
    """
    document = json.dumps(spec.schema(), indent=2)
    if output is None:
        typer.echo(document)
        return
    output.write_text(document + "\n", encoding="utf-8")
    typer.secho(f"wrote {output}", fg=typer.colors.GREEN)


@app.command()
def version() -> None:
    """Print the version and exit."""
    typer.echo(__version__)


if __name__ == "__main__":  # pragma: no cover
    app()
