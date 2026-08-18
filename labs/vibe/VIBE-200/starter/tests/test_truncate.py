from app.truncate import truncate_words


def test_truncate_shorter_than_limit():
    assert truncate_words("one two three", 5) == "one two three"


def test_truncate_adds_ellipsis():
    assert truncate_words("one two three four", 2) == "one two…"


def test_truncate_empty():
    assert truncate_words("", 3) == ""
