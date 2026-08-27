"""Word-level truncation helper for textkit (solution)."""


def truncate_words(text: str, limit: int) -> str:
    """Truncate text to at most `limit` words, adding an ellipsis when cut.

    Args:
        text: The source string.
        limit: Maximum number of words to keep.

    Returns:
        The original text when it has `limit` words or fewer; otherwise the
        first `limit` words joined by spaces with a trailing ellipsis.
        Returns "" for empty input.
    """
    if not text:
        return ""
    words = text.split()
    if len(words) <= limit:
        return " ".join(words)
    return " ".join(words[:limit]) + "…"
