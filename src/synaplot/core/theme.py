"""Colors used to fill the layers of a diagram."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

Color = str
"""A TikZ color expression.

TikZ accepts a mixing expression anywhere it accepts a color, so a value may
name a color, as in ``'teal'``, or mix several, as in ``'rgb:blue,5;green,15'``.
"""


class Theme(BaseModel):
    """The color used for each kind of layer.

    Every field except ``name`` is a colour expression. Build a variant by copying
    an existing theme and overriding the roles you want to change.

    Parameters
    ----------
    name
        Identifies the theme. Carried into a specification so a diagram can name
        the theme it was drawn with.
    conv, deconv, pool, unpool, fc, softmax, sum, concat, batchnorm
        Fill color for the layer of that name.
    conv_band, fc_band
        Color of the band drawn down the right of a convolution or a fully
        connected layer, which stands for the activation after it. The layer
        itself is filled with ``conv`` or ``fc``, so these color a part of a
        layer rather than a layer.
    edge
        Color of the arrows drawn between layers.

    Examples
    --------
    >>> theme = Theme()
    >>> theme.pool
    'rgb:red,1;black,0.3'

    Override one role and leave the rest alone:

    >>> mono = Theme(name="mono", conv="gray", pool="lightgray")
    >>> mono.conv, mono.softmax
    ('gray', 'rgb:magenta,5;black,7')
    """

    model_config = ConfigDict(frozen=True)

    name: str = "default"

    conv: Color = "rgb:yellow,5;red,2.5;white,5"
    conv_band: Color = "rgb:yellow,5;red,5;white,5"
    pool: Color = "rgb:red,1;black,0.3"
    unpool: Color = "rgb:blue,2;green,1;black,0.3"
    fc: Color = "rgb:blue,5;red,2.5;white,5"
    fc_band: Color = "rgb:blue,5;red,5;white,4"
    softmax: Color = "rgb:magenta,5;black,7"
    sum: Color = "rgb:blue,5;green,15"
    concat: Color = "rgb:blue,5;red,2.5;white,5"
    deconv: Color = "rgb:blue,5;green,2.5;white,5"
    batchnorm: Color = "rgb:yellow,5;black,3"
    edge: Color = "rgb:blue,4;red,1;green,4;black,3"

    def macro_definitions(self) -> str:
        r"""Return a ``\def`` line for every color in the theme.

        Returns
        -------
        str
            LaTeX definitions, one per line, for the preamble of the document.

        Examples
        --------
        >>> print(Theme().macro_definitions().splitlines()[0])
        \def\syColorConv{rgb:yellow,5;red,2.5;white,5}
        """
        return "\n".join(
            f"\\def\\{color_macro(field)}{{{getattr(self, field)}}}"
            for field in type(self).model_fields
            if field != "name"
        )


def color_macro(role: str) -> str:
    r"""Return the name of the LaTeX macro holding the color for a role.

    The name carries a ``sy`` prefix and contains only letters, so it can be
    used in the document body, where ``@`` is not a letter.

    Parameters
    ----------
    role
        A field name on :class:`Theme`, such as ``'conv_band'``.

    Returns
    -------
    str
        The macro name without its leading backslash.

    Examples
    --------
    >>> color_macro("conv")
    'syColorConv'
    >>> color_macro("conv_band")
    'syColorConvBand'
    """
    camel = "".join(part.capitalize() for part in role.split("_"))
    return f"syColor{camel}"
