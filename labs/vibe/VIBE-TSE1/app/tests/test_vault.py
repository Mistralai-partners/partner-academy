"""Base tests for the taskvault demo repo. These pass as shipped."""
import pytest

from app.vault import Vault


def test_add_and_all():
    v = Vault()
    v.add("Buy milk")
    v.add("Call Sam")
    assert [t.title for t in v.all()] == ["Buy milk", "Call Sam"]


def test_ids_increment():
    v = Vault()
    a = v.add("first")
    b = v.add("second")
    assert (a.id, b.id) == (1, 2)


def test_empty_title_rejected():
    v = Vault()
    with pytest.raises(ValueError):
        v.add("   ")
