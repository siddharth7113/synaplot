"""Checks the LaTeX a diagram produces, and that it compiles."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from importlib.resources import files
from pathlib import Path

import pytest

import synaplot as sp
from synaplot.core.theme import color_macro
from synaplot.latex.writer import (
    annotation_to_tikz,
    connection_to_tikz,
    diagram_to_tikz,
    style_source,
)
from synaplot.spec import layer_types

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


def test_a_diagram_that_flows_up_stacks_and_points_its_arrows_up():
    diagram = sp.Diagram(name="stack", flow="up", margin=0.5).add(
        sp.Block(name="a", text="a"), sp.Block(name="b", text="b")
    )
    diagram.connect("a", "b")
    _, attach = list(diagram.placements())[1]
    assert attach is not None
    assert attach.anchor is sp.Anchor.NORTH
    # Half of b's height, so the gap between the two is the margin.
    assert attach.offset.y == 0.5 + 12 * 0.2 / 2
    assert "(a-north) -- (b-south)" in diagram_to_tikz(diagram)


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
    # A box pic draws one box per entry in its width and reads the labels by
    # index, so four labels need four boxes or three of them go nowhere.
    assert "width={1,1,1,1}" in tikz


def test_a_width_given_per_box_is_left_alone():
    diagram = sp.Diagram().add(
        sp.Conv(name="c", filters=[64, 128], size=sp.Size(width=[2, 3]))
    )
    assert "width={2,3}" in diagram_to_tikz(diagram)


def test_a_skip_runs_level():
    """Both ends of a skip rise to the same height, so the run is horizontal."""
    tikz = diagram_to_tikz(small_diagram())
    levels = {
        line.split("|- 0,")[1].rstrip(");")
        for line in tikz.splitlines()
        if "|- 0," in line
    }
    assert len(levels) == 1


def test_every_caption_in_a_row_sits_on_one_line():
    tikz = diagram_to_tikz(small_diagram())
    # Every layer of the row is measured, captioned or not, because any of them
    # could be the one that reaches lowest.
    assert "\\syRowBase{syBaseline1}{conv1,pool1,conv2,out,add1}" in tikz
    assert tikz.count("\\syCaption{") == 2


def test_a_second_row_gets_a_line_of_its_own():
    diagram = sp.Diagram(name="rows").add(
        sp.Conv(name="conv1", caption="conv1"),
        sp.Conv(
            name="side1",
            caption="side 1",
            to=sp.Attach(layer="conv1", anchor=sp.Anchor.SOUTH, offset=sp.Offset(y=-8)),
        ),
    )
    tikz = diagram_to_tikz(diagram)
    assert "\\syRowBase{syBaseline1}{conv1}" in tikz
    assert "\\syRowBase{syBaseline2}{side1}" in tikz


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
    assert "(a-east) -- ++(2,0,0)" in first
    # The second leaves a corner, so the two do not share the run out, and it
    # comes back in on the side that corner names.
    assert "(b-northeast) -- ++(3.4,0,0)" in second
    assert "(c-east)" in second


def test_a_bypass_can_step_along_the_depth_axis():
    diagram = sp.Diagram(name="depth").add(
        sp.Conv(name="conv1"), sp.Conv(name="side1", to=sp.Attach(layer="conv1"))
    )
    diagram.connect(
        "conv1",
        "side1",
        style="bypass",
        source_anchor="near",
        target_anchor="west",
        clearance=6,
    )
    arrow = connection_to_tikz(diagram.connections[0], 0.0, diagram)
    assert "(conv1-near) -- ++(0,0,6)" in arrow
    # Depth is drawn across the page as well as down it, so there is no square
    # turn to make; the arrow runs straight to the target.
    assert "-- node[near end] {\\syArrow} (side1-west)" in arrow


def test_a_bypass_along_the_depth_axis_finds_its_own_lane():
    """The lane is where the target was placed, so nothing has to say it."""
    diagram = sp.Diagram(name="lane").add(
        sp.Conv(name="conv1"),
        sp.Conv(name="side1", to=sp.Attach(layer="conv1", offset=sp.Offset(z=40))),
    )
    diagram.connect(
        "conv1", "side1", style="bypass", source_anchor="near", target_anchor="west"
    )
    arrow = connection_to_tikz(diagram.connections[0], 0.0, diagram)
    # conv1 is 40 deep, so its near face already stands 4 out at scale 0.2 and
    # the step covers the rest of the way to the lane.
    assert "-- ++(0,0,36)" in arrow


def test_a_bypass_with_no_lane_to_find_steps_out_a_set_distance():
    diagram = sp.Diagram(name="side").add(
        sp.Block(name="a", text="a"),
        sp.Block(name="b", text="b", to=sp.Attach(layer="a", anchor=sp.Anchor.NORTH)),
    )
    diagram.connect("a", "b", style="bypass", source_anchor="east")
    arrow = connection_to_tikz(diagram.connections[0], 0.0, diagram)
    assert "-- ++(1.5,0,0)" in arrow


def test_a_bypass_can_leave_from_any_anchor_that_names_a_side():
    """An edge or a 3-D corner steps out to the side it names, like a corner."""
    diagram = sp.Diagram(name="edges").add(sp.Conv(name="a"), sp.Conv(name="b"))
    diagram.connect("a", "b", style="bypass", source_anchor="nearwest", clearance=1)
    arrow = connection_to_tikz(diagram.connections[0], 0.0, diagram)
    assert "(a-nearwest) -- ++(-1,0,0)" in arrow
    assert "(b-west)" in arrow


def test_a_bypass_cannot_leave_from_the_centre_of_a_layer():
    diagram = sp.Diagram(name="centre").add(sp.Conv(name="a"), sp.Conv(name="b"))
    diagram.connect("a", "b", style="bypass", source_anchor="anchor")
    with pytest.raises(ValueError, match="cannot leave from the centre of 'a'"):
        connection_to_tikz(diagram.connections[0], 0.0, diagram)


def test_a_layer_set_towards_the_reader_gets_a_caption_line_of_its_own():
    """TikZ draws depth diagonally, so a layer set forward is drawn lower."""
    diagram = sp.Diagram(name="lanes").add(
        sp.Conv(name="conv1", caption="conv1"),
        sp.Conv(
            name="side1",
            caption="side 1",
            to=sp.Attach(layer="conv1", offset=sp.Offset(z=20)),
        ),
    )
    tikz = diagram_to_tikz(diagram)
    assert "\\syRowBase{syBaseline1}{conv1}" in tikz
    assert "\\syRowBase{syBaseline2}{side1}" in tikz


def test_the_diagram_scale_reaches_every_pic():
    """Spacing layers for one scale and drawing them at another lines up nothing."""
    diagram = sp.Diagram(name="big", scale=0.4).add(sp.Conv(name="c"), sp.Sum(name="s"))
    assert diagram_to_tikz(diagram).count("scale=0.4") == 2


def test_an_annotation_points_at_its_layer_and_labels_the_far_end():
    diagram = sp.Diagram(name="loss").add(sp.Conv(name="loss"))
    diagram.annotate("loss", "$p$", offset=sp.Offset(y=0.25), reach=sp.Offset(x=-4))
    line = annotation_to_tikz(diagram.annotations[0])
    # The label hugs the arrow, above it and running back along it.
    assert "node[anchor=south west] {$p$}" in line
    assert line.endswith("([shift={(0,0.25,0)}] loss-west);")


def test_an_annotation_can_point_away_from_its_layer():
    diagram = sp.Diagram(name="loss").add(sp.Conv(name="loss"))
    diagram.annotate(
        "loss",
        "$g$",
        offset=sp.Offset(y=-0.25),
        reach=sp.Offset(x=-4),
        inward=False,
    )
    line = annotation_to_tikz(diagram.annotations[0])
    assert line.startswith("\\draw [syAnnotation] ([shift={(0,-0.25,0)}] loss-west) --")
    # Below the axis, so the label goes below the arrow rather than over it.
    assert line.endswith("++(-4,0,0) node[anchor=north west] {$g$};")


def test_an_annotation_that_is_not_offset_labels_beyond_the_end_of_its_arrow():
    """With no side of the line to sit on, a label over the line reads badly."""
    diagram = sp.Diagram(name="map").add(sp.Conv(name="box"))
    diagram.annotate("box", "north", anchor="north", reach=sp.Offset(y=3))
    diagram.annotate("box", "west", anchor="west", reach=sp.Offset(x=-4))
    above, beside = (annotation_to_tikz(a) for a in diagram.annotations)
    assert "node[anchor=south] {north}" in above
    assert "node[anchor=east] {west}" in beside


def test_annotating_a_layer_that_is_not_there_is_refused():
    with pytest.raises(KeyError, match="no layer named 'nobody'"):
        sp.Diagram(name="loss").add(sp.Conv(name="loss")).annotate("nobody", "$p$")


def test_a_legend_names_each_kind_of_layer_once():
    diagram = (
        sp.Diagram(name="key")
        .add(sp.Conv(name="c1"), sp.Conv(name="c2"), sp.Pool(name="p"))
        .add_legend()
    )
    assert [entry.label for entry in diagram.legend_entries()] == [
        "Convolution",
        "Pooling",
    ]
    assert "\\syLegendItem{\\syColorConv}{0.4}{Convolution}" in diagram_to_tikz(diagram)


def test_a_legend_leaves_out_a_layer_that_names_no_kind_of_thing():
    """A block carries its own text, so a key repeating it says nothing."""
    diagram = sp.Diagram(name="key").add(sp.Block(name="b", text="b")).add_legend()
    assert diagram.legend_entries() == []
    assert "syLegend" not in diagram_to_tikz(diagram)


def test_a_legend_is_pinned_clear_of_the_corner_it_names():
    diagram = (
        sp.Diagram(name="key").add(sp.Conv(name="c")).add_legend(position="north west")
    )
    assert "\\syLegend{north west}{south west}{1}" in diagram_to_tikz(diagram)


def test_a_legend_can_be_written_out_by_hand():
    diagram = sp.Diagram(name="key").add(sp.Conv(name="c"))
    diagram.legend = sp.Legend(entries=[sp.LegendEntry(label="mine", fill="teal")])
    assert "\\syLegendItem{{teal}}{0.7}{mine}" in diagram_to_tikz(diagram)


def test_a_layer_a_legend_names_is_filled_from_the_theme():
    """A layer in a legend needs a color to show, and the theme has to hold it."""
    for layer in layer_types().values():
        if layer.title:
            assert layer.role in sp.Theme.model_fields, layer.__name__


def test_every_color_in_the_theme_is_drawn_by_some_layer():
    """A color nothing draws with is a layer that was never written.

    Four of them sat unused for years upstream, which is how a fully connected
    layer and a normalization layer turned out to be missing.
    """
    drawn = {cls.role for cls in layer_types().values()}
    drawn |= {
        cls.band_role
        for cls in layer_types().values()
        if issubclass(cls, sp.layers.BandedBox)
    }
    named = set(sp.Theme.model_fields) - {"name", "edge"}
    assert named <= drawn


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


def test_every_anchor_is_a_coordinate_the_box_pic_defines():
    """Holds the Anchor enumeration to the pic it describes.

    The two are written in different languages and cannot import from one
    another, so nothing but this stops them drifting apart.
    """
    styles = files("synaplot.latex") / "styles" / "synaplot-box.sty"
    drawn = set(
        re.findall(
            r"\\coordinate \(\\sy@name-(\w+)\)", styles.read_text(encoding="utf-8")
        )
    )
    assert drawn == {anchor.value for anchor in sp.Anchor}


def _pic_source(styles: str, pic: str) -> str:
    """Return the definition of one pic, up to where the next one starts."""
    start = styles.index(f"{pic}/.pic=")
    rest = styles.find("/.pic=", start + len(pic) + 6)
    return styles[start:] if rest == -1 else styles[start:rest]


def test_every_layer_declares_the_anchors_its_pic_draws():
    """Holds each layer to the coordinates its own drawing defines.

    A ball has no corners and a flat shape has no depth. Attaching to an anchor
    a layer does not define is refused, so the list it declares has to be the
    list the drawing writes.
    """
    styles = style_source()
    for cls in layer_types().values():
        if not cls.pic:
            continue
        drawn = set(
            re.findall(
                r"\\coordinate \(\\sy@name-(\w+)\)", _pic_source(styles, cls.pic)
            )
        )
        declared = {anchor.value for anchor in cls.model_construct(name="x").anchors}
        assert declared == drawn, cls.__name__


def test_an_image_defines_the_anchors_it_declares():
    """An image is drawn as a node, so it writes its own coordinates out."""
    layer = sp.Input(name="img", path="cats.jpg")
    tikz = sp.Diagram(name="in").add(layer).to_tikz()
    drawn = set(re.findall(r"\\coordinate \(img-(\w+)\)", tikz))
    assert drawn == {anchor.value for anchor in layer.anchors}


def test_an_image_can_be_chained_from_and_connected_to():
    """Everything else addresses a layer as name-anchor, so an image must too."""
    diagram = sp.Diagram(name="in").add(
        sp.Input(name="img", path="cats.jpg"), sp.Conv(name="c")
    )
    diagram.connect("img", "c")
    tikz = diagram.to_tikz()
    assert "at (img-east)" in tikz
    assert "(img-east) -- node {\\syArrow} (c-west)" in tikz


def test_an_image_is_listed_as_a_file_the_drawing_reads():
    diagram = sp.Diagram(name="in").add(
        sp.Input(name="img", path="cats.jpg"), sp.Conv(name="c")
    )
    assert [str(asset) for asset in diagram.assets()] == ["cats.jpg"]


def test_a_name_tikz_cannot_use_is_refused():
    """TikZ reads 'layer1.0-east' as 'layer1' at an anchor that does not exist."""
    with pytest.raises(ValueError, match=r"'layer1\.0' cannot name a layer"):
        sp.Conv(name="layer1.0")
    for name in ("conv1", "layer1_0", "enc-1"):
        assert sp.Conv(name=name).name == name


def test_attaching_to_an_anchor_a_layer_does_not_define_is_refused():
    """LaTeX reports this as an unknown shape, deep inside its own log."""
    diagram = sp.Diagram(name="x").add(sp.Conv(name="c"), sp.Sum(name="add1"))
    diagram.connect("c", "add1", target_anchor="northeast")
    with pytest.raises(ValueError, match="'add1' defines: anchor, east"):
        diagram.to_tikz()


def test_naming_a_layer_that_is_not_in_the_diagram_is_refused():
    """A specification can name one; only building the diagram checks it."""
    from synaplot import spec

    diagram = spec.loads(
        "layers: [{kind: conv, name: a}]\nconnections: [{source: a, target: ghost}]"
    )
    with pytest.raises(ValueError, match="'ghost', which is not a layer"):
        diagram.to_tikz()


def test_styles_keep_their_macros_private():
    assert "\\sy@" in style_source()
    assert "caption/.store      in=\\caption" not in style_source()


def test_every_theme_color_a_style_reads_is_one_the_theme_defines():
    """A style names a theme macro directly, and only the theme can define it."""
    read = set(re.findall(r"\\syColor(\w+)", style_source()))
    defined = {
        color_macro(field).removeprefix("syColor")
        for field in sp.Theme.model_fields
        if field != "name"
    }
    assert read and read <= defined


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
