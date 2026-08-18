"""Tests for the search(keyword) feature (see FEATURE.md).

In the live demo, Vibe Code writes both app/vault.py::search and this file.
This is the reference version.
"""
from app.vault import Vault


def _seed() -> Vault:
    v = Vault()
    v.add("Buy milk")
    v.add("buy bread")
    v.add("Call Sam")
    return v


def test_search_matches_substring():
    v = _seed()
    assert {t.title for t in v.search("buy")} == {"Buy milk", "buy bread"}


def test_search_is_case_insensitive():
    v = _seed()
    assert len(v.search("BUY")) == 2


def test_search_empty_keyword_returns_nothing():
    v = _seed()
    assert v.search("   ") == []
