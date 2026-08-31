"""The programs synaplot knows how to drive.

Each class here wraps one external program. Subclass :class:`Renderer` or
:class:`Converter` to teach synaplot another one; the pipeline finds it through
the base class, so there is no list to keep up to date.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from synaplot.render.base import Converter, Format, Renderer, ToolchainError

if TYPE_CHECKING:
    from pathlib import Path

APT = "run: sudo apt install"
BREW = "run: brew install"


class Tectonic(Renderer):
    """Compiles with tectonic.

    Preferred over the other renderers because it is a single program that
    downloads the LaTeX packages a document asks for, so it works without a
    full TeX installation.
    """

    name: ClassVar[str] = "tectonic"
    priority: ClassVar[int] = 0
    install_hints: ClassVar[dict[str, str]] = {
        "Linux": "run: curl -fsSL https://drop-sh.fullyjustified.net | sh",
        "Darwin": f"{BREW} tectonic",
        "Windows": "run: winget install TectonicProject.Tectonic",
    }

    @classmethod
    def to_pdf(cls, source: Path, output_dir: Path) -> Path:
        """Compile a LaTeX file with tectonic."""
        cls.run(["-X", "compile", "--outdir", str(output_dir), str(source)])
        return output_dir / f"{source.stem}.pdf"


class LatexEngine(Renderer):
    """Compiles with a LaTeX engine from a TeX installation.

    Attributes
    ----------
    passes : int
        How many times to run the engine. Two passes let TikZ resolve
        coordinates that are only known after everything has been placed once.
    """

    passes: ClassVar[int] = 2
    install_hints: ClassVar[dict[str, str]] = {
        "Linux": f"{APT} texlive-latex-extra texlive-fonts-extra",
        "Darwin": f"{BREW} --cask mactex",
        "Windows": "install MiKTeX from https://miktex.org/download",
    }

    @classmethod
    def to_pdf(cls, source: Path, output_dir: Path) -> Path:
        """Compile a LaTeX file, running the engine :attr:`passes` times."""
        for _ in range(cls.passes):
            cls.run(
                [
                    "-interaction=nonstopmode",
                    "-halt-on-error",
                    f"-output-directory={output_dir}",
                    str(source),
                ]
            )
        return output_dir / f"{source.stem}.pdf"


class LuaLaTeX(LatexEngine):
    """Compiles with lualatex."""

    name: ClassVar[str] = "lualatex"
    priority: ClassVar[int] = 10


class XeLaTeX(LatexEngine):
    """Compiles with xelatex."""

    name: ClassVar[str] = "xelatex"
    priority: ClassVar[int] = 20


class PdfLaTeX(LatexEngine):
    """Compiles with pdflatex."""

    name: ClassVar[str] = "pdflatex"
    priority: ClassVar[int] = 30


class Dvisvgm(Converter):
    """Converts a PDF to SVG with dvisvgm.

    Preferred for SVG because it keeps the text as text with the fonts embedded.
    The other converters trace every character into a path, which produces a
    much larger file.
    """

    name: ClassVar[str] = "dvisvgm"
    priority: ClassVar[int] = 0
    produces: ClassVar[frozenset[Format]] = frozenset({Format.SVG})
    install_hints: ClassVar[dict[str, str]] = {
        "Linux": f"{APT} texlive-extra-utils",
        "Darwin": f"{BREW} dvisvgm",
        "Windows": "install MiKTeX from https://miktex.org/download",
    }

    @classmethod
    def convert(cls, pdf: Path, target: Path, fmt: Format, dpi: int) -> Path:
        """Convert a PDF to SVG."""
        cls.run(["--pdf", "--font-format=woff", f"--output={target}", str(pdf)])
        return target


class Pdftocairo(Converter):
    """Converts a PDF to SVG or PNG with pdftocairo, part of poppler."""

    name: ClassVar[str] = "pdftocairo"
    priority: ClassVar[int] = 10
    produces: ClassVar[frozenset[Format]] = frozenset({Format.SVG, Format.PNG})
    install_hints: ClassVar[dict[str, str]] = {
        "Linux": f"{APT} poppler-utils",
        "Darwin": f"{BREW} poppler",
        "Windows": "install poppler from https://github.com/oschwartz10612/poppler-windows",
    }

    @classmethod
    def convert(cls, pdf: Path, target: Path, fmt: Format, dpi: int) -> Path:
        """Convert a PDF to SVG or PNG."""
        if fmt is Format.SVG:
            cls.run(["-svg", str(pdf), str(target)])
            return target
        if fmt is Format.PNG:
            # pdftocairo appends the extension itself, so it is given the name
            # without one.
            cls.run(
                [
                    "-png",
                    "-r",
                    str(dpi),
                    "-singlefile",
                    str(pdf),
                    str(target.with_suffix("")),
                ]
            )
            return target
        raise ToolchainError(f"{cls.name} cannot write {fmt.value} files")
