"""Checks drawing a diagram from a PyTorch model."""

from __future__ import annotations

import base64
from pathlib import Path

import pytest

torch = pytest.importorskip("torch")

from torch import nn  # noqa: E402

import synaplot as sp  # noqa: E402
from synaplot import spec  # noqa: E402
from synaplot.pytorch import Call, Sizing, from_torch, layer_for, trace  # noqa: E402


class Residual(nn.Module):
    """A basic block: two convolutions, the input added back, one ReLU used twice."""

    def __init__(self) -> None:
        super().__init__()
        self.conv1 = nn.Conv2d(8, 8, 3, padding=1)
        self.bn1 = nn.BatchNorm2d(8)
        self.relu = nn.ReLU(inplace=True)
        self.conv2 = nn.Conv2d(8, 8, 3, padding=1)
        self.bn2 = nn.BatchNorm2d(8)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out = self.relu(self.bn1(self.conv1(x)))
        out = self.bn2(self.conv2(out))
        out += x
        return self.relu(out)


class Net(nn.Module):
    """A stem, a stage of two residual blocks, pooling, and a classifier."""

    def __init__(self) -> None:
        super().__init__()
        self.stem = nn.Sequential(nn.Conv2d(3, 8, 3, stride=2, padding=1), nn.ReLU())
        self.stage = nn.Sequential(Residual(), Residual())
        self.pool = nn.AdaptiveAvgPool2d(1)
        self.fc = nn.Linear(8, 10)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.pool(self.stage(self.stem(x)))
        return self.fc(torch.flatten(x, 1))


class UShape(nn.Module):
    """An encoder, a decoder, and a concatenation joining them."""

    def __init__(self) -> None:
        super().__init__()
        self.enc = nn.Conv2d(3, 8, 3, padding=1)
        self.down = nn.MaxPool2d(2)
        self.mid = nn.Conv2d(8, 16, 3, padding=1)
        self.up = nn.Upsample(scale_factor=2)
        self.dec = nn.Conv2d(24, 4, 3, padding=1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        skip = self.enc(x)
        deep = self.up(self.mid(self.down(skip)))
        return self.dec(torch.cat([deep, skip], dim=1))


class Keyworded(nn.Module):
    """A model called with keyword arguments, as a Hugging Face model is."""

    def __init__(self) -> None:
        super().__init__()
        self.embed = nn.Embedding(20, 8)
        self.head = nn.Linear(8, 3)

    def forward(
        self, input_ids: torch.Tensor, attention_mask: torch.Tensor | None = None
    ) -> torch.Tensor:
        hidden = self.embed(input_ids)
        if attention_mask is not None:
            hidden = hidden * attention_mask[..., None]
        return self.head(hidden.mean(dim=1))


def kinds(diagram: sp.Diagram) -> list[str]:
    return [type(layer).__name__ for layer in diagram.layers]


def test_every_leaf_is_drawn_with_the_shape_it_produced():
    diagram = from_torch(Net(), torch.randn(1, 3, 32, 32), depth=None)
    assert kinds(diagram)[:3] == ["ConvRelu", "Conv", "BatchNorm"]
    stem = diagram["stem_0"]
    assert stem.filters == 8
    assert stem.spatial == 16
    assert stem.caption == "stem.0"
    assert diagram["fc"].units == 10
    assert kinds(diagram)[-2:] == ["Pool", "FullyConnected"]


def test_a_residual_add_is_drawn_as_a_sum_reached_by_a_skip():
    diagram = from_torch(Net(), torch.randn(1, 3, 32, 32), depth=None)
    sums = [layer.name for layer in diagram.layers if isinstance(layer, sp.Sum)]
    assert sums == ["add", "add_2"]
    skips = [
        (c.source, c.target)
        for c in diagram.connections
        if c.style is sp.ConnectionStyle.SKIP
    ]
    # The first block adds the stem's output back on; the second adds the
    # first block's, which its activation, undrawn, stands in for.
    assert skips == [("stem_0", "add"), ("add", "add_2")]


def test_a_module_used_twice_is_two_calls():
    names = [call.name for call in trace(Net(), torch.randn(1, 3, 32, 32)).calls]
    assert "stage_0_relu" in names
    assert "stage_0_relu_2" in names


def test_depth_draws_a_stage_as_one_box():
    diagram = from_torch(Net(), torch.randn(1, 3, 32, 32), depth=1)
    assert kinds(diagram) == ["Conv", "Conv", "Pool", "FullyConnected"]
    assert [layer.name for layer in diagram.layers] == ["stem", "stage", "pool", "fc"]
    assert diagram["stage"].filters == 8
    # Every arrow is forward: the additions inside the stage are its own.
    assert {c.style for c in diagram.connections} == {sp.ConnectionStyle.FORWARD}


def test_a_concatenation_is_drawn_as_a_concat_reached_by_a_skip():
    diagram = from_torch(UShape(), torch.randn(1, 3, 16, 16))
    assert kinds(diagram) == ["Conv", "Pool", "Conv", "Unpool", "Concat", "Conv"]
    skip = next(c for c in diagram.connections if c.style is sp.ConnectionStyle.SKIP)
    assert (skip.source, skip.target) == ("enc", "cat")


def test_a_model_called_with_keyword_arguments():
    ids = torch.randint(0, 20, (1, 5))
    diagram = from_torch(
        Keyworded(), {"input_ids": ids, "attention_mask": torch.ones(1, 5)}
    )
    assert kinds(diagram) == ["Block", "FullyConnected"]
    assert diagram["embed"].text == "embed"


def test_a_transformer_is_drawn_as_blocks_and_sums():
    layer = nn.TransformerEncoderLayer(16, 2, 32, batch_first=True)
    encoder = nn.TransformerEncoder(layer, num_layers=1)
    diagram = from_torch(encoder, torch.randn(1, 5, 16), depth=3)
    assert "Block" in kinds(diagram)
    assert kinds(diagram).count("Sum") == 2


def test_sizes_follow_the_logarithm_of_the_shape():
    sizing = Sizing()
    assert sizing.box((1, 64, 112, 112), largest=224) == sp.Size(
        width=2, height=34, depth=34
    )
    assert sizing.box((1, 512, 7, 7), largest=224) == sp.Size(
        width=5, height=10, depth=10
    )
    assert sizing.box((1, 3, 1, 1), largest=224).height == sizing.smallest
    assert sizing.bar(4096).depth == 30
    assert sizing.bar(4).depth == 2 * sizing.smallest


def test_a_handler_of_your_own_is_used():
    class Gate(nn.Module):
        def forward(self, x: torch.Tensor) -> torch.Tensor:
            return x * 2

    # Named explicitly, because a class local to a function cannot be found
    # from its annotation once annotations are strings.
    @layer_for.register(Gate)
    def _(module: Gate, call: Call) -> sp.Layer:
        return sp.Operator(name=call.name, symbol=r"$\otimes$")

    model = nn.Sequential(nn.Conv2d(3, 4, 3), Gate())
    diagram = from_torch(model, torch.randn(1, 3, 8, 8))
    assert kinds(diagram) == ["Conv", "Operator"]


def test_the_diagram_survives_the_yaml_round_trip():
    diagram = from_torch(Net(), torch.randn(1, 3, 32, 32))
    again = spec.loads(spec.dumps(diagram))
    assert again.to_tikz() == diagram.to_tikz()


def test_the_model_is_left_as_it_was():
    model = Net().train()
    from_torch(model, torch.randn(1, 3, 32, 32))
    assert model.training
    assert not any(
        hasattr(m, "_forward_hooks") and m._forward_hooks for m in model.modules()
    )


def test_an_image_is_drawn_and_run(tmp_path: Path, monkeypatch):
    pytest.importorskip("PIL")
    monkeypatch.chdir(tmp_path)
    # A 1x1 PNG, so the test needs no image checked in beside it.
    Path("pixel.png").write_bytes(
        base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8"
            "z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
        )
    )
    diagram = from_torch(Net(), image="pixel.png", depth=1)
    assert kinds(diagram)[0] == "Input"
    assert (diagram.connections[0].source, diagram.connections[0].target) == (
        "input",
        "stem",
    )


def test_from_torch_needs_something_to_run_on():
    with pytest.raises(ValueError, match="needs inputs"):
        from_torch(Net())


def test_from_torch_is_reached_from_the_package():
    assert sp.from_torch is from_torch
