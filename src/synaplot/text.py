"""Helpers for text that ends up in LaTeX."""

from __future__ import annotations

# Each character LaTeX treats specially, mapped to the form that prints it.
# str.maketrans translates in one pass, so the braces this table introduces in
# \textbackslash{} are not themselves escaped a second time.
_REPLACEMENTS = str.maketrans(
    {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
)


def escape(text: str) -> str:
    r"""Escape text so LaTeX prints it literally.

    Captions and labels are read as LaTeX, so ``$3\times3$`` renders as math.
    That is usually what you want when you write the text yourself. Use this
    when the text comes from somewhere else, such as a layer name read from a
    model, where a stray ``_`` or ``%`` would break the build.

    Parameters
    ----------
    text
        The text to escape.

    Returns
    -------
    str
        The text with every character that LaTeX treats specially replaced.

    Examples
    --------
    >>> escape("conv_1")
    'conv\\_1'
    >>> escape("50% dropout")
    '50\\% dropout'
    >>> escape("a & b")
    'a \\& b'

    Math is escaped too, so do not use this on text you wrote as LaTeX:

    >>> escape("$3\\times3$")
    '\\$3\\textbackslash{}times3\\$'
    """
    return text.translate(_REPLACEMENTS)
