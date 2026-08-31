"""Compiles a diagram to PDF, SVG, PNG, or LaTeX source.

The work is split between a :class:`~synaplot.render.base.Renderer`, which
compiles LaTeX into a PDF, and a :class:`~synaplot.render.base.Converter`,
which turns that PDF into an image. Each one carries a priority, and the
installed one with the lowest priority is used.

To add another program, subclass :class:`~synaplot.render.base.Renderer` or
:class:`~synaplot.render.base.Converter` and set ``name`` to the program to run.
Both are found by walking their base class, so there is no list to add it to.
"""

from __future__ import annotations

import tempfile
from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING

from synaplot.render import tools as _tools  # noqa: F401  (defines the built-in tools)
from synaplot.render.base import (
    Converter,
    Format,
    Renderer,
    Tool,
    ToolchainError,
)

if TYPE_CHECKING:
    from synaplot.core.diagram import Diagram

__all__ = [
    "Converter",
    "Format",
    "Renderer",
    "Tool",
    "ToolchainError",
    "converters",
    "render",
    "renderers",
    "toolchain",
]


def _subclasses(base: type[Tool]) -> list[type[Tool]]:
    """Return every named class below a base, nearest first, without repeats."""
    found: dict[str, type[Tool]] = {}
    stack = list(base.__subclasses__())
    while stack:
        cls = stack.pop()
        stack.extend(cls.__subclasses__())
        if cls.name:
            found.setdefault(cls.__qualname__, cls)
    return sorted(found.values(), key=lambda cls: (cls.priority, cls.name))  # type: ignore[attr-defined]


def renderers(*, installed_only: bool = True) -> list[type[Renderer]]:
    """Return the renderers synaplot can use, most preferred first.

    Parameters
    ----------
    installed_only
        Whether to leave out renderers whose program is not on the PATH.

    Returns
    -------
    list of type of Renderer
        Renderers in the order they would be tried.
    """
    found = [cls for cls in _subclasses(Renderer) if issubclass(cls, Renderer)]
    return [cls for cls in found if cls.available()] if installed_only else found


def converters(
    fmt: Format | None = None, *, installed_only: bool = True
) -> list[type[Converter]]:
    """Return the converters synaplot can use, most preferred first.

    Parameters
    ----------
    fmt
        Keep only converters that write this format. ``None`` keeps them all.
    installed_only
        Whether to leave out converters whose program is not on the PATH.

    Returns
    -------
    list of type of Converter
        Converters in the order they would be tried.
    """
    found = [cls for cls in _subclasses(Converter) if issubclass(cls, Converter)]
    if fmt is not None:
        found = [cls for cls in found if fmt in cls.produces]
    return [cls for cls in found if cls.available()] if installed_only else found


def toolchain() -> list[tuple[type[Tool], bool]]:
    """Return every program synaplot knows about and whether it is installed.

    Returns
    -------
    list of tuple of (type of Tool, bool)
        Each program and whether it was found on the PATH. Renderers come
        first, then converters, each most preferred first.
    """
    known = renderers(installed_only=False) + converters(installed_only=False)
    return [(cls, cls.available()) for cls in known]


def _missing(what: str, options: Sequence[type[Tool]]) -> ToolchainError:
    """Return an error naming what to install to get past a missing program."""
    lines = [f"no program is installed that can {what}.", "Install one of:"]
    lines += [f"  {cls.name}: {cls.install_hint()}" for cls in options]
    return ToolchainError("\n".join(lines))


def render(
    diagram: Diagram,
    path: str | Path,
    *,
    fmt: Format | str | None = None,
    dpi: int = 300,
    renderer: type[Renderer] | None = None,
) -> Path:
    """Write a diagram to a file.

    The format comes from the file's suffix unless ``fmt`` says otherwise.
    Writing LaTeX needs no external program; every other format is compiled in
    a temporary directory, and only the finished file is copied out.

    Parameters
    ----------
    diagram
        The diagram to write.
    path
        Where to write it.
    fmt
        Format to write. ``None`` reads it from the suffix of ``path``.
    dpi
        Resolution for PNG output.
    renderer
        Use this renderer instead of the most preferred installed one.

    Returns
    -------
    Path
        The file that was written.

    Raises
    ------
    ToolchainError
        If no installed program can produce the requested format. The message
        names what to install.
    """
    target = Path(path)
    chosen = Format(fmt) if fmt is not None else Format.from_path(target)
    target.parent.mkdir(parents=True, exist_ok=True)

    source = diagram.to_tex()
    if chosen is Format.TEX:
        target.write_text(source, encoding="utf-8")
        return target

    engines = [renderer] if renderer is not None else renderers()
    if not engines:
        raise _missing("compile LaTeX", renderers(installed_only=False))

    converter: type[Converter] | None = None
    if chosen is not Format.PDF:
        available = converters(chosen)
        if not available:
            raise _missing(
                f"convert a PDF to {chosen.value}",
                converters(chosen, installed_only=False),
            )
        converter = available[0]

    with tempfile.TemporaryDirectory(prefix="synaplot-") as directory:
        work = Path(directory)
        tex = work / f"{diagram.name}.tex"
        tex.write_text(source, encoding="utf-8")
        pdf = engines[0].to_pdf(tex, work)
        if converter is None:
            target.write_bytes(pdf.read_bytes())
        else:
            converter.convert(pdf, work / target.name, chosen, dpi)
            target.write_bytes((work / target.name).read_bytes())
    return target
