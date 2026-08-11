"""ncurses rendering of the dungeon grid with entity overlay."""

import curses

from frogue.core.components import Position, Renderable
from frogue.core.fov import Explored, Fov
from frogue.dungeon.map import WALL

DARK_GRAY = 236
DIM_GRAY = 240


def render(stdscr, world, grid: list[list[str]], depth: int = 1, turns: int = 0) -> None:
    """Draw the grid, then overlay entities on top, then the status line."""
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, -1, -1)
    curses.init_pair(2, -1, DARK_GRAY)
    curses.init_pair(3, DIM_GRAY, -1)
    stdscr.clear()
    max_y, max_x = stdscr.getmaxyx()
    visible = world.resources.get(Fov)
    explored = world.resources.get(Explored)
    for y, row in enumerate(grid):
        if y >= max_y:
            break
        for x, cell in enumerate(row):
            if x >= max_x:
                break
            state = _cell_state(x, y, visible, explored)
            if state is None:
                continue
            pair = _pair_for(cell, state)
            stdscr.addstr(y, x, cell, curses.color_pair(pair))
    for _eid, pos, rend in world.query(Position, Renderable):
        if pos.y >= max_y or pos.x >= max_x:
            continue
        state = _cell_state(pos.x, pos.y, visible, explored)
        if state is None:
            continue
        pair = _pair_for(rend.char, state)
        stdscr.addstr(pos.y, pos.x, rend.char, curses.color_pair(pair))
    _draw_status(stdscr, grid, depth, turns, max_y, max_x)
    stdscr.refresh()


def _draw_status(
    stdscr, grid: list[list[str]], depth: int, turns: int, max_y: int, max_x: int
) -> None:
    """Draw the depth and turn counter below the map, if it fits."""
    y = len(grid) + 1
    if y >= max_y:
        return
    status = f"Depth: {depth}   Turn: {turns}"
    stdscr.addstr(y, 0, status[:max_x])


def _cell_state(x: int, y: int, visible, explored) -> str | None:
    """Return 'visible', 'explored', or None for a cell."""
    if visible is not None and (x, y) in visible.cells:
        return "visible"
    if explored is not None and (x, y) in explored.cells:
        return "explored"
    return None


def _pair_for(cell: str, state: str) -> int:
    """Return the color pair for a cell given its visibility state."""
    if state == "explored":
        return 3
    if cell == WALL:
        return 2
    return 1
