"""Keeps doctest collection off the modules whose optional dependency is absent."""

from importlib.util import find_spec

collect_ignore = [] if find_spec("torch") else ["src/synaplot/pytorch.py"]
