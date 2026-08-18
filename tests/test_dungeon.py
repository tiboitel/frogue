"""Tests for dungeon generation."""

from frogue.dungeon import DOWN, EXIT, EXIT_DEPTH, UP, floor_seed, generate
from frogue.dungeon.map import EMPTY, FLOOR
from frogue.dungeon.rect import Rect


def _floor_cells(grid: list[list[str]]) -> set[tuple[int, int]]:
    """Return all floor cells in the grid."""
    return {(x, y) for y, row in enumerate(grid) for x, cell in enumerate(row) if cell == FLOOR}


def _unpack(result):
    """Unpack generate() result, ignoring stairs."""
    grid, rooms, _stairs = result
    return grid, rooms


def _reachable(grid: list[list[str]], start: tuple[int, int]) -> set[tuple[int, int]]:
    """Return all floor cells reachable from start via 4-way moves."""
    seen: set[tuple[int, int]] = set()
    stack = [start]
    height = len(grid)
    width = len(grid[0])
    while stack:
        x, y = stack.pop()
        if (x, y) in seen or not (0 <= x < width and 0 <= y < height):
            continue
        if grid[y][x] != FLOOR:
            continue
        seen.add((x, y))
        stack.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
    return seen


def test_generates_nine_rooms() -> None:
    """The dungeon should contain exactly nine rooms."""
    _grid, rooms = _unpack(generate(seed=1))
    assert len(rooms) == 9


def test_rooms_use_even_sizes() -> None:
    """Room sizes should be even to avoid parallel corridors."""
    _grid, rooms = _unpack(generate(seed=1))
    for room in rooms:
        assert room.w % 2 == 0
        assert room.h % 2 == 0


def test_all_rooms_connected() -> None:
    """Every room should be reachable from every other room."""
    grid, rooms = _unpack(generate(seed=1))
    start = (rooms[0].x + 1, rooms[0].y + 1)
    reachable = _reachable(grid, start)
    for room in rooms:
        assert (room.x + 1, room.y + 1) in reachable


def test_rooms_fit_within_areas() -> None:
    """Each room should fit inside its 3x3 area."""
    _grid, rooms = _unpack(generate(seed=1))
    for i, room in enumerate(rooms):
        area = Rect(1 + (i % 3) * 10, 1 + (i // 3) * 8, 10, 8)
        assert area.contains(room.x, room.y)
        assert area.contains(room.right - 1, room.bottom - 1)


def test_deterministic_with_seed() -> None:
    """Same seed should produce the same dungeon."""
    grid_a, _ = _unpack(generate(seed=42))
    grid_b, _ = _unpack(generate(seed=42))
    assert grid_a == grid_b


def test_no_floor_adjacent_to_void() -> None:
    """No floor cell should be bordered by empty void."""
    for seed in range(20):
        grid, _ = _unpack(generate(seed=seed))
        for y, row in enumerate(grid):
            for x, cell in enumerate(row):
                if cell == FLOOR:
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < len(row) and 0 <= ny < len(grid):
                            assert grid[ny][nx] != EMPTY


def test_walls_all_touch_floor() -> None:
    """Every wall cell should have a floor neighbour in 8 directions."""
    for seed in range(20):
        grid, _ = _unpack(generate(seed=seed))
        for y, row in enumerate(grid):
            for x, cell in enumerate(row):
                if cell == "#":
                    assert _touches_floor_diag(grid, x, y)


def _touches_floor_diag(grid: list[list[str]], x: int, y: int) -> bool:
    """Return True if any of the 8 neighbours of the cell is floor."""
    for dx, dy in (
        (1, 0),
        (-1, 0),
        (0, 1),
        (0, -1),
        (1, 1),
        (1, -1),
        (-1, 1),
        (-1, -1),
    ):
        nx, ny = x + dx, y + dy
        if 0 <= nx < len(grid[0]) and 0 <= ny < len(grid) and grid[ny][nx] == FLOOR:
            return True
    return False


def test_floor_one_has_only_down_stair() -> None:
    """Depth 1 should have exactly one down stair and no up stair."""
    _grid, _rooms, stairs = generate(seed=1, depth=1, max_depth=5)
    assert len(stairs) == 1
    assert stairs[0].direction == DOWN
    assert stairs[0].to_depth == 2


def test_last_floor_has_up_and_exit_stair() -> None:
    """Depth 5 should have one up stair and one exit stair."""
    _grid, _rooms, stairs = generate(seed=1, depth=5, max_depth=5)
    assert len(stairs) == 2
    directions = {s.direction for s in stairs}
    assert directions == {UP, EXIT}
    up = next(s for s in stairs if s.direction == UP)
    assert up.to_depth == 4
    exit_stair = next(s for s in stairs if s.direction == EXIT)
    assert exit_stair.to_depth == EXIT_DEPTH


def test_middle_floors_have_both_stairs() -> None:
    """Depths 2-4 should have one up and one down stair."""
    for depth in (2, 3, 4):
        _grid, _rooms, stairs = generate(seed=1, depth=depth, max_depth=5)
        assert len(stairs) == 2
        assert {s.direction for s in stairs} == {UP, DOWN}


def test_stairs_in_opposite_rooms() -> None:
    """Up and down stairs should sit in opposite (or adjacent) compass rooms."""
    _grid, rooms, stairs = generate(seed=1, depth=3, max_depth=5)
    cells = {room: ((room.x - 1) // 10, (room.y - 1) // 8) for room in rooms}
    down = next(s for s in stairs if s.direction == DOWN)
    up = next(s for s in stairs if s.direction == UP)
    down_room = next(r for r in rooms if r.x <= down.x < r.right and r.y <= down.y < r.bottom)
    up_room = next(r for r in rooms if r.x <= up.x < r.right and r.y <= up.y < r.bottom)
    dc, dr = cells[down_room]
    uc, ur = cells[up_room]
    assert (uc, ur) != (dc, dr)
    if (dc, dr) == (1, 1):
        assert max(abs(uc - dc), abs(ur - dr)) == 1
    else:
        assert (uc, ur) == (2 - dc, 2 - dr)


def test_floor_seed_deterministic() -> None:
    """Same world seed and depth should produce identical floors."""
    grid_a, _rooms_a, stairs_a = generate(seed=floor_seed(42, 3), depth=3, max_depth=5)
    grid_b, _rooms_b, stairs_b = generate(seed=floor_seed(42, 3), depth=3, max_depth=5)
    assert grid_a == grid_b
    assert stairs_a == stairs_b
