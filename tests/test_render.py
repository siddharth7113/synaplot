"""Checks format handling, tool discovery, and what happens when tools are missing."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from typer.testing import CliRunner

import synaplot as sp
from synaplot.cli import app
from synaplot.render import (
    Converter,
    Format,
    Renderer,
    ToolchainError,
    converters,
    render,
    renderers,
    toolchain,
)
from synaplot.render.tools import Dvisvgm, Pdftocairo, Tectonic

runner = CliRunner()


def tiny() -> sp.Diagram:
    return sp.Diagram(name="tiny").add(sp.Conv(name="conv1", filters=8, spatial=32))


def test_format_comes_from_the_suffix():
    assert Format.from_path("a/b/c.svg") is Format.SVG
    assert Format.from_path(Path("diagram.PDF")) is Format.PDF


def test_an_unknown_suffix_lists_what_is_supported():
    with pytest.raises(ValueError, match="synaplot writes tex, pdf, svg, png"):
        Format.from_path("diagram.gif")


def test_tools_are_found_through_their_base_class():
    """Discovery walks the base classes, so there is no list to maintain."""
    assert Tectonic in renderers(installed_only=False)
    assert Dvisvgm in converters(installed_only=False)
    assert Pdftocairo in converters(Format.PNG, installed_only=False)
    # dvisvgm writes SVG only, so it must not be offered for PNG.
    assert Dvisvgm not in converters(Format.PNG, installed_only=False)


def test_the_preferred_tool_comes_first():
    assert renderers(installed_only=False)[0] is Tectonic
    assert converters(Format.SVG, installed_only=False)[0] is Dvisvgm


def test_a_subclass_joins_the_discovery():
    class Imaginary(Renderer):
        name = "imaginary-engine"

        @classmethod
        def to_pdf(cls, source: Path, output_dir: Path) -> Path:
            raise NotImplementedError

    assert Imaginary in renderers(installed_only=False)
    assert Imaginary not in renderers()


def test_toolchain_reports_every_tool():
    reported = {cls.name for cls, _ in toolchain()}
    assert {"tectonic", "pdflatex", "dvisvgm", "pdftocairo"} <= reported


def test_writing_latex_needs_no_external_program(tmp_path: Path):
    written = render(tiny(), tmp_path / "out.tex")
    assert written.read_text(encoding="utf-8").startswith("\\documentclass")


def test_a_missing_converter_says_what_to_install(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(Converter, "available", classmethod(lambda cls: False))
    with pytest.raises(ToolchainError) as error:
        render(tiny(), tmp_path / "out.svg")
    message = str(error.value)
    assert "convert a PDF to svg" in message
    assert "dvisvgm" in message and "pdftocairo" in message
    # The point of the message is that it tells you the command to run.
    assert "install" in message.lower()


def test_a_missing_renderer_says_what_to_install(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(Renderer, "available", classmethod(lambda cls: False))
    with pytest.raises(ToolchainError) as error:
        render(tiny(), tmp_path / "out.pdf")
    assert "compile LaTeX" in str(error.value)
    assert "tectonic" in str(error.value)


def test_doctor_lists_tools_and_formats():
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
    for name in ("tectonic", "dvisvgm", "pdftocairo"):
        assert name in result.stdout
    for fmt in ("tex", "pdf", "svg", "png"):
        assert fmt in result.stdout


def test_the_cli_writes_latex(tmp_path: Path):
    source = tmp_path / "arch.py"
    source.write_text(
        "import synaplot as sp\n"
        "diagram = sp.Diagram(name='arch').add(sp.Conv(name='c', filters=8))\n",
        encoding="utf-8",
    )
    output = tmp_path / "arch.tex"
    result = runner.invoke(app, ["render", str(source), "-o", str(output)])
    assert result.exit_code == 0, result.stdout
    assert output.is_file()


def test_the_cli_explains_a_file_with_no_diagram(tmp_path: Path):
    source = tmp_path / "empty.py"
    source.write_text("x = 1\n", encoding="utf-8")
    result = runner.invoke(app, ["render", str(source), "-o", str(tmp_path / "x.tex")])
    assert result.exit_code == 1
    assert "does not leave a Diagram" in result.stderr


def test_the_cli_reports_an_error_raised_by_the_file(tmp_path: Path):
    source = tmp_path / "broken.py"
    source.write_text("raise ValueError('bad shape')\n", encoding="utf-8")
    result = runner.invoke(app, ["render", str(source), "-o", str(tmp_path / "x.tex")])
    assert result.exit_code == 1
    assert "ValueError" in result.stderr
    assert "bad shape" in result.stderr


@pytest.mark.render
@pytest.mark.skipif(
    not os.environ.get("SYNAPLOT_RENDER_TESTS"),
    reason="set SYNAPLOT_RENDER_TESTS=1 to compile diagrams",
)
@pytest.mark.parametrize("suffix", ["pdf", "svg", "png"])
def test_every_format_is_written(tmp_path: Path, suffix: str):
    if not renderers():
        pytest.skip("no LaTeX engine is installed")
    if suffix != "pdf" and not converters(Format(suffix)):
        pytest.skip(f"no converter for {suffix} is installed")
    written = render(tiny(), tmp_path / f"out.{suffix}")
    assert written.stat().st_size > 0


@pytest.mark.render
@pytest.mark.skipif(
    not os.environ.get("SYNAPLOT_RENDER_TESTS"),
    reason="set SYNAPLOT_RENDER_TESTS=1 to compile diagrams",
)
def test_nothing_is_left_behind(tmp_path: Path):
    """Compiling happens in a temporary directory, so only the output remains."""
    if not renderers():
        pytest.skip("no LaTeX engine is installed")
    render(tiny(), tmp_path / "out.pdf")
    assert [p.name for p in tmp_path.iterdir()] == ["out.pdf"]
