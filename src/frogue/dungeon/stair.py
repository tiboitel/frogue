"""Stair placement for dungeon floors."""

from dataclasses import dataclass

from .rect import Rect

UP = "up"
DOWN = "down"

AREA_W = 10
AREA_H = 8
BORDER = 1


@dataclass(frozen=True)
class Stair:
    """A stair cell linking two floors."""

    x: int
    y: int
    direction: str
    to_depth: int


def place_stairs(rng, rooms: list[Rect], depth: int, max_depth: int) -> list[Stair]:
    """Return the stairs for a floor, placed in opposite compass rooms."""
    cells = _compass_cells(rooms)
    stairs: list[Stair] = []
    down_room: Rect | None = None
    if depth < max_depth:
        down_room = rng.choice(rooms)
        stairs.append(_make_stair(down_room, DOWN, depth + 1))
    if depth > 1:
        up_room = _opposite_room(rng, rooms, cells, down_room)
        stairs.append(_make_stair(up_room, UP, depth - 1))
    return stairs


def _make_stair(room: Rect, direction: str, to_depth: int) -> Stair:
    """Create a stair at the center of a room."""
    return Stair(room.x + room.w // 2, room.y + room.h // 2, direction, to_depth)


def _compass_cells(rooms: list[Rect]) -> dict[Rect, tuple[int, int]]:
    """Map each room to its (col, row) cell in the 3x3 area grid."""
    return {room: ((room.x - BORDER) // AREA_W, (room.y - BORDER) // AREA_H) for room in rooms}


def _opposite_room(
    rng, rooms: list[Rect], cells: dict[Rect, tuple[int, int]], exclude: Rect | None
) -> Rect:
    """Return the room in the compass cell opposite to the excluded room."""
    if exclude is None:
        return rng.choice(rooms)
    target = (2 - cells[exclude][0], 2 - cells[exclude][1])
    if cells[exclude] == target:
        return _nudge(rng, rooms, cells, exclude)
    for room in rooms:
        if cells[room] == target:
            return room
    return _nearest_room(rooms, cells, target)


def _nudge(rng, rooms: list[Rect], cells: dict[Rect, tuple[int, int]], exclude: Rect) -> Rect:
    """Return a room adjacent to the excluded center room."""
    col, row = cells[exclude]
    candidates = [
        room
        for room in rooms
        if cells[room] != (col, row)
        and max(abs(cells[room][0] - col), abs(cells[room][1] - row)) == 1
    ]
    return rng.choice(candidates)


def _nearest_room(
    rooms: list[Rect], cells: dict[Rect, tuple[int, int]], target: tuple[int, int]
) -> Rect:
    """Return the room closest to the target compass cell."""
    return min(rooms, key=lambda room: _dist(cells[room], target))


def _dist(a: tuple[int, int], b: tuple[int, int]) -> int:
    """Return the Manhattan distance between two compass cells."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])
