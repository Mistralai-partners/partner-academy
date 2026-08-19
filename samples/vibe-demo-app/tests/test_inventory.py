from app.inventory import add_item, total_quantity, ITEMS


def test_add_and_total():
    ITEMS.clear()
    add_item("a", 2)
    add_item("a", 3)
    add_item("b", 1)
    assert total_quantity() == 6
