"""Map grid and tile constants."""

WALL = "#"
FLOOR = "."
EMPTY = " "


def empty_map(width: int, height: int) -> list[list[str]]:
    """Return a width x height grid filled with empty tiles."""
    return [[EMPTY for _ in range(width)] for _ in range(height)]


def add_walls(grid: list[list[str]]) -> None:
    """Turn empty cells adjacent to floor into walls.

    Walls hug the shape of rooms and corridors, ensuring every floor cell is
    bordered by a wall and never open to the void. Only cells touching floor
    become walls, so no stray fragments are generated in the void.
    """
    height = len(grid)
    width = len(grid[0])
    for y in range(height):
        for x in range(width):
            if grid[y][x] == EMPTY and _touches_floor(grid, x, y):
                grid[y][x] = WALL


def _touches_floor(grid: list[list[str]], x: int, y: int) -> bool:
    """Return True if any of the 8 neighbours of the cell is floor."""
    height = len(grid)
    width = len(grid[0])
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
        if 0 <= nx < width and 0 <= ny < height and grid[ny][nx] == FLOOR:
            return True
    return False


def carve_room(grid: list[list[str]], room) -> None:
    """Fill a room's interior with floor tiles."""
    for y in range(room.y, room.bottom):
        for x in range(room.x, room.right):
            grid[y][x] = FLOOR


def carve_corridor(grid: list[list[str]], a: tuple[int, int], b: tuple[int, int]) -> None:
    """Carve an L-shaped corridor from point a to point b.

    Overwrites empty tiles so the corridor always reaches its destination.
    """
    ax, ay = a
    bx, by = b
    if ax <= bx:
        _carve_h(grid, ax, bx, ay)
        _carve_v(grid, ay, by, bx)
    else:
        _carve_v(grid, ay, by, ax)
        _carve_h(grid, ax, bx, by)


def _carve_h(grid: list[list[str]], x1: int, x2: int, y: int) -> None:
    """Carve a horizontal corridor row, overwriting empty tiles."""
    for x in range(min(x1, x2), max(x1, x2) + 1):
        if grid[y][x] == EMPTY:
            grid[y][x] = FLOOR


def _carve_v(grid: list[list[str]], y1: int, y2: int, x: int) -> None:
    """Carve a vertical corridor column, overwriting empty tiles."""
    for y in range(min(y1, y2), max(y1, y2) + 1):
        if grid[y][x] == EMPTY:
            grid[y][x] = FLOOR
