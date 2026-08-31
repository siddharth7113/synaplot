"""Checks the LaTeX a diagram produces, and that it compiles."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

import synaplot as sp
from synaplot.latex.writer import (
    connection_to_tikz,
    diagram_to_tikz,
    style_source,
)

EXPECTED = Path(__file__).parent / "expected"


def small_diagram() -> sp.Diagram:
    """Return a diagram exercising all three pic types and both arrow styles."""
    diagram = sp.Diagram(name="small", gap=1.6)
    diagram.add(
        sp.Conv(name="conv1", filters=64, spatial=512, caption="conv1"),
        sp.Pool(name="pool1"),
        sp.ConvRelu(
            name="conv2",
            filters=[128, 128, 128],
            spatial=256,
            size=sp.Size(width=[3, 3, 3], height=30, depth=30),
        ),
        sp.Softmax(name="out", classes=10, caption="softmax"),
        sp.Sum(name="add1"),
    )
    diagram.connect("conv1", "pool1")
    diagram.connect("pool1", "conv2")
    diagram.connect("conv2", "out")
    diagram.connect("out", "add1")
    diagram.connect("conv1", "out", style="skip")
    return diagram


def test_tikz_matches_the_saved_output():
    """Compares the TikZ a diagram writes against a checked-in copy.

    Set ``SYNAPLOT_UPDATE_EXPECTED=1`` to rewrite the saved copy after a change
    you meant to make, then read the diff before committing it.
    """
    saved = EXPECTED / "small.tikz"
    # The saved copy ends in a newline, as a text file does, and as the
    # end-of-file-fixer hook would make it anyway.
    produced = diagram_to_tikz(small_diagram()) + "\n"
    if os.environ.get("SYNAPLOT_UPDATE_EXPECTED"):
        saved.parent.mkdir(exist_ok=True)
        saved.write_text(produced, encoding="utf-8")
    assert produced == saved.read_text(encoding="utf-8")


def test_first_layer_sits_at_the_origin_and_the_rest_chain():
    diagram = small_diagram()
    placements = list(diagram.placements())
    assert placements[0][1] is None
    assert placements[1][1] is not None
    assert placements[1][1].layer == "conv1"


def test_an_explicit_position_is_kept():
    diagram = sp.Diagram()
    diagram.add(sp.Conv(name="a"))
    diagram.add(sp.Conv(name="b", to=sp.Attach(layer="a", anchor=sp.Anchor.NORTH)))
    assert list(diagram.placements())[1][1].anchor is sp.Anchor.NORTH


def test_every_filter_is_drawn():
    """PlotNeuralNet drew only the first two entries of a filter list."""
    diagram = sp.Diagram().add(sp.ConvRelu(name="c", filters=[64, 128, 256, 512]))
    tikz = diagram_to_tikz(diagram)
    for value in ("64", "128", "256", "512"):
        assert f'"{value}"' in tikz


def test_a_skip_runs_level():
    """Both ends of a skip rise to the same height, so the run is horizontal."""
    tikz = diagram_to_tikz(small_diagram())
    levels = {
        line.split("|- 0,")[1].rstrip(");")
        for line in tikz.splitlines()
        if "|- 0," in line
    }
    assert len(levels) == 1


def test_every_caption_sits_on_one_line():
    tikz = diagram_to_tikz(small_diagram())
    assert tikz.startswith("\\coordinate (syBaseline) at (0,")
    # The deepest layer decides where the line goes, and every captioned layer
    # is aligned to it rather than to itself.
    assert tikz.count("baseline=syBaseline") == 5


def test_a_drawing_with_no_captions_needs_no_baseline():
    diagram = sp.Diagram(name="quiet").add(sp.Conv(name="conv1"), sp.Pool(name="p1"))
    assert "baseline" not in diagram_to_tikz(diagram)


def test_an_arrow_into_a_flat_layer_ends_in_an_arrowhead():
    diagram = sp.Diagram(name="flat").add(
        sp.Block(name="a", text="a"),
        sp.Operator(name="b", to=sp.Attach(layer="a", anchor=sp.Anchor.NORTH)),
        sp.Conv(name="c"),
    )
    diagram.connect("a", "b")
    diagram.connect("b", "c")
    into_flat, into_volume = (
        connection_to_tikz(c, 0.0, diagram) for c in diagram.connections
    )
    assert "syHead" in into_flat and "syArrow" not in into_flat
    assert "syArrow" in into_volume and "syHead" not in into_volume


def test_the_lines_of_a_full_connection_go_behind_the_layers():
    diagram = sp.Diagram(name="mesh").add(
        sp.Dense(name="a", nodes=2), sp.Dense(name="b", nodes=2)
    )
    diagram.connect("a", "b", style="full")
    tikz = diagram_to_tikz(diagram)
    assert "\\begin{pgfonlayer}{syBackground}" in tikz
    assert tikz.count("syEdge") == 4


def test_two_bypasses_can_leave_one_layer_in_different_lanes():
    diagram = sp.Diagram(name="lanes").add(
        sp.Block(name="a", text="a"),
        sp.Block(name="b", text="b", to=sp.Attach(layer="a", anchor=sp.Anchor.NORTH)),
        sp.Block(name="c", text="c", to=sp.Attach(layer="b", anchor=sp.Anchor.NORTH)),
    )
    diagram.connect("a", "b", style="bypass", source_anchor="east", clearance=2)
    diagram.connect("b", "c", style="bypass", source_anchor="northeast", clearance=3.4)
    first, second = (connection_to_tikz(c, 0.0, diagram) for c in diagram.connections)
    assert "(a-east) -- ++(2,0)" in first
    # The second leaves a corner, so the two do not share the run out, and it
    # comes back in on the side that corner names.
    assert "(b-northeast) -- ++(3.4,0)" in second
    assert "(c-east)" in second


def test_the_document_carries_its_own_styles():
    """A standalone document needs no style files beside it."""
    tex = small_diagram().to_tex()
    assert "\\subimport" not in tex
    assert "Box/.pic" in tex
    assert tex.count("\\documentclass") == 1


def test_a_fragment_has_no_document_wrapper():
    tex = small_diagram().to_tex(standalone=False)
    assert "\\documentclass" not in tex
    assert "\\begin{document}" not in tex
    assert "\\begin{tikzpicture}" in tex


def test_styles_keep_their_macros_private():
    assert "\\sy@" in style_source()
    assert "caption/.store      in=\\caption" not in style_source()


@pytest.mark.render
@pytest.mark.skipif(
    not os.environ.get("SYNAPLOT_RENDER_TESTS"),
    reason="set SYNAPLOT_RENDER_TESTS=1 to compile diagrams",
)
def test_the_diagram_compiles(tmp_path: Path):
    """Compiles the diagram and checks its labels reach the page.

    Reading the text layer catches a diagram that compiles but draws the wrong
    thing. Comparing images instead would fail on any font or TeX version
    change.
    """
    tectonic = shutil.which("tectonic")
    if tectonic is None:
        pytest.skip("tectonic is not installed")

    source = tmp_path / "small.tex"
    source.write_text(small_diagram().to_tex(), encoding="utf-8")
    subprocess.run(
        [tectonic, "-X", "compile", "--outdir", str(tmp_path), str(source)],
        check=True,
        capture_output=True,
        timeout=600,
    )
    pdf = tmp_path / "small.pdf"
    assert pdf.stat().st_size > 0

    pdftotext = shutil.which("pdftotext")
    if pdftotext is None:
        pytest.skip("poppler-utils is not installed")
    text = subprocess.run(
        [pdftotext, str(pdf), "-"],
        check=True,
        capture_output=True,
        text=True,
        timeout=120,
    ).stdout
    # Depth labels are drawn along a sloped edge, and pdftotext breaks rotated
    # text across lines, so compare with the whitespace taken out.
    flat = "".join(text.split())
    for label in ("conv1", "softmax", "64", "512", "128", "10"):
        assert label in flat, f"{label!r} is missing from the rendered page"
