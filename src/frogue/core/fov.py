"""Field of view: line-of-sight, vision computation, and resources."""

from dataclasses import dataclass, field

from hive.core import System

from .collision import is_blocked
from .components import Controllable, Position, Vision
from .input import GridSize


@dataclass
class Fov:
    """Resource holding the set of currently visible cells."""

    cells: set[tuple[int, int]] = field(default_factory=set)


@dataclass
class Explored:
    """Resource holding the set of cells the player has ever seen."""

    cells: set[tuple[int, int]] = field(default_factory=set)


def has_line_of_sight(world, x0: int, y0: int, x1: int, y1: int) -> bool:
    """Return True if no impassable entity lies between the two points.

    The observer's own cell and the target cell are always reachable, even
    if they are walls or occupied by an impassable entity.
    """
    for x, y in _ray(x0, y0, x1, y1):
        if (x, y) == (x0, y0):
            continue
        if (x, y) == (x1, y1):
            return True
        if is_blocked(world, x, y):
            return False
    return True


def compute_vision(world, px: int, py: int, radius: int) -> set[tuple[int, int]]:
    """Return cells within radius that have line of sight to the player."""
    size = world.resources.get(GridSize)
    if size is None:
        raise RuntimeError("GridSize resource not registered")
    visible: set[tuple[int, int]] = set()
    for y in range(max(0, py - radius), min(size.height, py + radius + 1)):
        for x in range(max(0, px - radius), min(size.width, px + radius + 1)):
            if (x - px) ** 2 + (y - py) ** 2 <= radius**2 and has_line_of_sight(
                world, px, py, x, y
            ):
                visible.add((x, y))
    return visible


def _ray(x0: int, y0: int, x1: int, y1: int) -> list[tuple[int, int]]:
    """Return the cells along a Bresenham line from (x0, y0) to (x1, y1)."""
    cells: list[tuple[int, int]] = []
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    x, y = x0, y0
    while True:
        cells.append((x, y))
        if (x, y) == (x1, y1):
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x += sx
        if e2 <= dx:
            err += dx
            y += sy
    return cells


class VisionSystem(System):
    """Compute the player's field of view and update visibility resources."""

    def update(self, world, dispatcher) -> None:
        for _eid, pos, vision, _ctrl in world.query(Position, Vision, Controllable):
            visible = compute_vision(world, pos.x, pos.y, vision.radius)
            world.resources.register(Fov(visible))
            explored = world.resources.get(Explored)
            if explored is None:
                explored = Explored()
                world.resources.register(explored)
            explored.cells |= visible
