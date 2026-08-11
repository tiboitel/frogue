"""Random helpers for dungeon generation."""

from random import Random

from .rect import Rect


def random_even_point(rng: Random, rect: Rect) -> tuple[int, int]:
    """Return a random even-coordinate point inside the rectangle.

    Even coordinates keep corridors from running parallel to room edges.
    """
    x = rng.randrange(rect.x, rect.right, 2)
    y = rng.randrange(rect.y, rect.bottom, 2)
    return x, y


def random_even_room(rng: Random, area: Rect, min_size: int = 4) -> Rect:
    """Return a random even-sized room that fits inside the area."""
    max_w = (area.w - min_size) // 2
    max_h = (area.h - min_size) // 2
    w = min_size + 2 * rng.randint(0, max_w)
    h = min_size + 2 * rng.randint(0, max_h)
    x = area.x + 2 * rng.randint(0, (area.w - w) // 2)
    y = area.y + 2 * rng.randint(0, (area.h - h) // 2)
    return Rect(x, y, w, h)
