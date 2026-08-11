"""Collision checks shared by movement and field of view."""

from frogue.dungeon.map import EMPTY

from .components import Impassable, Position
from .input import Grid


def is_blocked(world, x: int, y: int) -> bool:
    """Return True if the cell is void or occupied by an impassable entity."""
    grid = world.resources.get(Grid)
    if grid is not None and grid.cells[y][x] == EMPTY:
        return True
    return any(pos.x == x and pos.y == y for _eid, pos, _ in world.query(Position, Impassable))
