from app.slugify import slugify


def test_slugify_basic():
    assert slugify("Hello, World!") == "hello-world"


def test_slugify_collapses_and_strips():
    assert slugify("  Multiple   Spaces -- and  dashes!! ") == "multiple-spaces-and-dashes"
