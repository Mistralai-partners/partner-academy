"""Casing helpers for textkit.

This is the PATTERN FILE for the package. Every helper here is a pure
function: it takes a string, guards empty input, carries type hints and a
Google-style docstring, and returns a transformed string. When you add a new
helper, follow this shape so the codebase stays consistent.
"""
import re


def to_snake_case(text: str) -> str:
    """Convert an arbitrary string to snake_case.

    Args:
        text: The source string.

    Returns:
        The snake_cased string, or "" for empty input.
    """
    if not text:
        return ""
    words = re.findall(r"[A-Za-z0-9]+", text)
    return "_".join(w.lower() for w in words)
