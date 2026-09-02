# Installation

synaplot is not on PyPI yet. Install it from a checkout:

```console
git clone https://github.com/siddharth7113/synaplot
pip install ./synaplot
```

That is enough to write LaTeX source. Producing a PDF or an image needs a LaTeX
engine, and producing an SVG or a PNG needs a converter as well.

To see what you have, run:

```console
synaplot doctor
```

It lists every program synaplot can use, marks the ones it found, says which
formats work, and gives the install command for the rest. Each LaTeX engine it
finds is tried on a one-layer diagram, so `found` means the engine works: a
program on the PATH can still lack a package every diagram needs, and `doctor`
prints the line LaTeX complained on rather than leaving you to find it.

## LaTeX engines

synaplot uses the first of these it finds. To compile with another one, name
it: `synaplot render arch.yaml -o arch.pdf --renderer pdflatex`.

| Program | Notes |
| --- | --- |
| `tectonic` | Recommended. One program, no TeX installation, downloads the packages a document asks for. |
| `lualatex`, `xelatex`, `pdflatex` | Used if you already have a TeX installation. |

Installing tectonic:

```console
# Linux
curl -fsSL https://drop-sh.fullyjustified.net | sh

# macOS
brew install tectonic

# Windows
winget install TectonicProject.Tectonic
```

## Converters

Needed only for SVG and PNG output.

| Program | Writes | Notes |
| --- | --- | --- |
| `dvisvgm` | SVG | Preferred. Keeps the text as text, which gives a much smaller file. |
| `pdftocairo` | SVG, PNG | Part of poppler. Traces each character into a path. |

```console
# Linux
sudo apt install texlive-extra-utils poppler-utils

# macOS
brew install dvisvgm poppler
```

## Adding another program

Subclass {class}`~synaplot.render.Renderer` or
{class}`~synaplot.render.Converter` and set `name` to the program to run.
synaplot finds it by walking the base class, so there is nothing to register.

```python
from pathlib import Path

from synaplot.render import Renderer


class Latexmk(Renderer):
    name = "latexmk"
    priority = 5

    @classmethod
    def to_pdf(cls, source: Path, output_dir: Path) -> Path:
        cls.run(["-pdf", f"-outdir={output_dir}", str(source)])
        return output_dir / f"{source.stem}.pdf"
```
