"""What a rendering tool is, and what to say when one is missing."""

from __future__ import annotations

import platform
import shutil
import subprocess
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import ClassVar


class Format(str, Enum):
    """An output format synaplot can produce.

    Examples
    --------
    >>> Format("svg").value
    'svg'
    >>> Format.from_path("diagram.PNG")
    <Format.PNG: 'png'>
    """

    TEX = "tex"
    PDF = "pdf"
    SVG = "svg"
    PNG = "png"

    @classmethod
    def from_path(cls, path: str | Path) -> Format:
        """Return the format named by a file's suffix.

        Parameters
        ----------
        path
            A file name or path.

        Returns
        -------
        Format
            The matching format.

        Raises
        ------
        ValueError
            If the suffix is not one synaplot writes.
        """
        suffix = str(path).rsplit(".", 1)[-1].lower()
        try:
            return cls(suffix)
        except ValueError:
            known = ", ".join(f.value for f in cls)
            raise ValueError(
                f"cannot write {suffix!r} files; synaplot writes {known}"
            ) from None


class ToolchainError(RuntimeError):
    """Raised when the programs needed to render are missing or fail."""


class Tool:
    """An external program synaplot runs.

    Subclasses name the program and say what it does. Two kinds derive from
    this: a :class:`Renderer` compiles LaTeX into a PDF, and a
    :class:`Converter` turns that PDF into an image.

    Attributes
    ----------
    name : str
        The program to look for on the PATH.
    install_hints : dict
        Maps a platform, as returned by :func:`platform.system`, to the command
        that installs the program there.
    """

    name: ClassVar[str] = ""
    install_hints: ClassVar[dict[str, str]] = {}

    @classmethod
    def path(cls) -> str | None:
        """Return the full path to the program, or ``None`` if it is not found."""
        return shutil.which(cls.name)

    @classmethod
    def available(cls) -> bool:
        """Return whether the program is installed."""
        return cls.path() is not None

    @classmethod
    def install_hint(cls) -> str:
        """Return how to install the program on this machine.

        Returns
        -------
        str
            A command to run, or a note that no hint is known for the platform.
        """
        hint = cls.install_hints.get(platform.system())
        return hint or f"see the {cls.name} documentation for install steps"

    @classmethod
    def run(cls, arguments: list[str], *, timeout: int = 600) -> str:
        """Run the program and return what it wrote to standard output.

        Parameters
        ----------
        arguments
            Arguments to pass, not including the program itself.
        timeout
            Seconds to wait before giving up.

        Returns
        -------
        str
            The program's standard output.

        Raises
        ------
        ToolchainError
            If the program is missing, fails, or does not finish in time. The
            message carries the program's own output, which is where LaTeX
            reports what it disliked.
        """
        executable = cls.path()
        if executable is None:
            raise ToolchainError(
                f"{cls.name} is not installed. To install it, {cls.install_hint()}."
            )
        try:
            finished = subprocess.run(
                [executable, *arguments],
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as error:
            raise ToolchainError(
                f"{cls.name} did not finish within {timeout} seconds"
            ) from error
        if finished.returncode != 0:
            output = (finished.stderr or finished.stdout).strip()
            raise ToolchainError(f"{cls.name} failed:\n{output}")
        return finished.stdout


class Renderer(Tool, ABC):
    """Compiles a LaTeX document into a PDF.

    Attributes
    ----------
    priority : int
        Which renderer to prefer when several are installed. Lower comes first.
    """

    priority: ClassVar[int] = 100

    @classmethod
    @abstractmethod
    def to_pdf(cls, source: Path, output_dir: Path) -> Path:
        """Compile a LaTeX file and return the PDF it produced.

        Parameters
        ----------
        source
            The ``.tex`` file to compile.
        output_dir
            Directory to write the PDF and any intermediate files into.

        Returns
        -------
        Path
            The PDF that was written.
        """


class Converter(Tool, ABC):
    """Turns a PDF into an image.

    Attributes
    ----------
    produces : frozenset of Format
        The formats this converter can write.
    priority : int
        Which converter to prefer when several are installed. Lower comes
        first.
    """

    produces: ClassVar[frozenset[Format]] = frozenset()
    priority: ClassVar[int] = 100

    @classmethod
    @abstractmethod
    def convert(cls, pdf: Path, target: Path, fmt: Format, dpi: int) -> Path:
        """Convert a PDF and return the file that was written.

        Parameters
        ----------
        pdf
            The PDF to read.
        target
            Where to write the result.
        fmt
            The format to write.
        dpi
            Resolution for raster output. Ignored when writing SVG.

        Returns
        -------
        Path
            The file that was written.
        """
