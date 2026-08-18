"""Data model for a stocked item."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Item:
    """A single stocked item.

    Attributes:
        sku: Stock-keeping unit identifier.
        stock_level: Units currently on hand.
        threshold: Reorder trigger point. When stock reaches this level or
            drops below it, the item should be reordered.
        target: Desired stock level to restore up to when reordering.
    """

    sku: str
    stock_level: int
    threshold: int
    target: int

    def __post_init__(self) -> None:
        if self.stock_level < 0:
            raise ValueError("stock_level must not be negative")
        if self.threshold < 0:
            raise ValueError("threshold must not be negative")
        if self.target < self.threshold:
            raise ValueError("target must be at least the threshold")
