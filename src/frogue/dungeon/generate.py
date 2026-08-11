"""Simple Rogue-style dungeon generation."""

from random import Random

from .map import FLOOR, add_walls, carve_corridor, carve_room, empty_map
from .random import random_even_point, random_even_room
from .rect import Rect
from .stair import Stair, place_stairs

GRID_W = 3
GRID_H = 3
AREA_W = 10
AREA_H = 8
MIN_ROOM = 4
BORDER = 1


def _areas() -> list[Rect]:
    """Return the 3x3 predefined non-overlapping areas, inset by the border."""
    return [
        Rect(
            BORDER + c * AREA_W,
            BORDER + r * AREA_H,
            AREA_W,
            AREA_H,
        )
        for r in range(GRID_H)
        for c in range(GRID_W)
    ]


def _place_rooms(rng: Random, areas: list[Rect]) -> list[Rect]:
    """Place one random room in each area."""
    return [random_even_room(rng, area, MIN_ROOM) for area in areas]


def _connect_rooms(grid: list[list[str]], rng: Random, rooms: list[Rect]) -> None:
    """Carve corridors linking each room to a random prior room."""
    shuffled = rooms[:]
    rng.shuffle(shuffled)
    for i in range(1, len(shuffled)):
        a = random_even_point(rng, shuffled[i])
        b = random_even_point(rng, shuffled[i - 1])
        carve_corridor(grid, a, b)


def generate(
    seed: int | None = None, depth: int = 1, max_depth: int = 5
) -> tuple[list[list[str]], list[Rect], list[Stair]]:
    """Generate a dungeon floor, returning the grid, rooms, and stairs."""
    rng = Random(seed)
    areas = _areas()
    rooms = _place_rooms(rng, areas)
    grid = empty_map(GRID_W * AREA_W + 2 * BORDER, GRID_H * AREA_H + 2 * BORDER)
    _connect_rooms(grid, rng, rooms)
    for room in rooms:
        carve_room(grid, room)
    add_walls(grid)
    stairs = place_stairs(rng, rooms, depth, max_depth)
    _carve_stairs(grid, stairs)
    return grid, rooms, stairs


def _carve_stairs(grid: list[list[str]], stairs: list[Stair]) -> None:
    """Carve stair cells as floor so they are walkable."""
    for stair in stairs:
        grid[stair.y][stair.x] = FLOOR


def floor_seed(world_seed: int | None, depth: int) -> int | None:
    """Derive a deterministic per-floor seed from the world seed."""
    if world_seed is None:
        return None
    return (world_seed * 1009 + depth) % (2**32)
