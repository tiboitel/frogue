"""Rectangle helpers for dungeon layout."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Rect:
    """Axis-aligned rectangle: top-left corner, width, height."""

    x: int
    y: int
    w: int
    h: int

    @property
    def right(self) -> int:
        """Right edge (exclusive)."""
        return self.x + self.w

    @property
    def bottom(self) -> int:
        """Bottom edge (exclusive)."""
        return self.y + self.h

    def contains(self, px: int, py: int) -> bool:
        """Return True if point lies inside the rectangle."""
        return self.x <= px < self.right and self.y <= py < self.bottom
