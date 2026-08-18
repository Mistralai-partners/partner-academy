"""URL-slug helper for textkit.

BUG (intentional): some inputs come out with doubled hyphens or a hyphen
hanging off the start or end. The two tests in tests/test_slugify.py show the
symptom. Task 2 hands this to Vibe to fix; you confirm by running the suite.
"""
import re


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "-", text.lower())
