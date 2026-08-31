"""Checks reading and writing a diagram as YAML or JSON."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

import synaplot as sp
from synaplot import spec
from synaplot.cli import app
from synaplot.core.base import Layer

runner = CliRunner()

EXAMPLES = Path(__file__).parent.parent / "examples"

DOCUMENT = """
name: tiny
layers:
  - {kind: conv, name: conv1, filters: [64, 64], spatial: 224, caption: conv1}
  - {kind: pool, name: pool1}
  - {kind: sum, name: add1}
connections:
  - {source: conv1, target: pool1}
  - {source: conv1, target: add1, style: skip}
"""


def test_every_layer_with_a_kind_can_be_named():
    """Checked by property rather than by a list, which would drift."""
    kinds = spec.layer_types()
    for kind, cls in kinds.items():
        assert issubclass(cls, Layer)
        assert cls.model_fields["kind"].default == kind
    # A few that must always be there, covering each drawing style.
    assert {"conv", "pool", "sum", "dense", "block"} <= set(kinds)


def test_shared_bases_are_not_offered_as_kinds():
    """A base such as BoxLayer has no kind, so it cannot be named."""
    assert sp.layers.BoxLayer not in spec.layer_types().values()
    assert sp.layers.FilteredBox not in spec.layer_types().values()


def test_loading_builds_the_right_classes():
    diagram = spec.loads(DOCUMENT)
    assert [type(layer).__name__ for layer in diagram.layers] == [
        "Conv",
        "Pool",
        "Sum",
    ]
    assert diagram["conv1"].filters == [64, 64]
    assert diagram.connections[1].style is sp.ConnectionStyle.SKIP


def test_a_round_trip_keeps_every_field():
    """Serializing must not drop the fields a specific layer adds."""
    original = spec.loads(DOCUMENT)
    again = spec.loads(spec.dumps(original))
    assert again["conv1"].filters == original["conv1"].filters
    assert again["conv1"].spatial == original["conv1"].spatial
    assert again.to_tikz() == original.to_tikz()


def test_json_is_read_and_written():
    original = spec.loads(DOCUMENT)
    text = spec.dumps(original, as_json=True)
    assert json.loads(text)["layers"][0]["kind"] == "conv"
    assert spec.loads(text).to_tikz() == original.to_tikz()


def test_a_missing_kind_lists_the_choices():
    with pytest.raises(ValueError, match="a layer needs a kind"):
        spec.loads("layers: [{name: mystery}]")


def test_an_unknown_kind_lists_the_choices():
    with pytest.raises(ValueError, match="unknown layer kind 'attention'"):
        spec.loads("layers: [{kind: attention, name: a}]")


def test_a_document_that_is_not_a_mapping_is_refused():
    with pytest.raises(ValueError, match="must be a mapping"):
        spec.loads("- just\n- a\n- list\n")


def test_the_schema_covers_every_kind():
    document = spec.schema()
    variants = document["properties"]["layers"]["items"]["oneOf"]
    assert len(variants) == len(spec.layer_types())


def test_every_reference_in_the_schema_resolves():
    document = spec.schema()
    text = json.dumps(document)
    referenced = {part.split('"')[0] for part in text.split('"#/$defs/')[1:]}
    assert referenced <= set(document["$defs"])


@pytest.mark.parametrize("name", sorted(path.name for path in EXAMPLES.glob("*.yaml")))
def test_the_examples_load_and_write_tikz(name: str):
    """Every example must stay loadable, so none can quietly rot."""
    diagram = spec.load(EXAMPLES / name)
    assert diagram.layers
    assert diagram.to_tikz()


def test_the_cli_renders_a_specification(tmp_path: Path):
    source = tmp_path / "arch.yaml"
    source.write_text(DOCUMENT, encoding="utf-8")
    output = tmp_path / "arch.tex"
    result = runner.invoke(app, ["render", str(source), "-o", str(output)])
    assert result.exit_code == 0, result.stdout
    assert "tikzpicture" in output.read_text(encoding="utf-8")


def test_the_cli_reports_a_bad_specification(tmp_path: Path):
    source = tmp_path / "bad.yaml"
    source.write_text("layers: [{kind: nope, name: a}]", encoding="utf-8")
    result = runner.invoke(app, ["render", str(source), "-o", str(tmp_path / "x.tex")])
    assert result.exit_code == 1
    assert "unknown layer kind" in result.stderr


def test_the_cli_converts_python_to_a_specification(tmp_path: Path):
    output = tmp_path / "lenet.yaml"
    result = runner.invoke(
        app, ["convert", str(EXAMPLES / "lenet.py"), "-o", str(output)]
    )
    assert result.exit_code == 0, result.stdout
    assert spec.load(output).name == "lenet"


def test_the_cli_prints_the_schema():
    result = runner.invoke(app, ["schema"])
    assert result.exit_code == 0
    assert json.loads(result.stdout)["title"] == "synaplot diagram"
