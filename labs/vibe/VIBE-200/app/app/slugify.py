"""URL-slug helper for textkit (solution)."""
import re


def slugify(text: str) -> str:
    """Convert an arbitrary string to a URL slug.

    Args:
        text: The source string.

    Returns:
        A lowercase, hyphen-separated slug with runs of non-alphanumeric
        characters collapsed to a single hyphen and no leading or trailing
        hyphen. Returns "" for empty input.
    """
    if not text:
        return ""
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower())
    return slug.strip("-")
