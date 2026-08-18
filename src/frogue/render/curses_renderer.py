"""ncurses rendering of the dungeon grid with entity overlay."""

import curses

from frogue.core.components import Controllable, Life, Position, Renderable
from frogue.core.fov import Explored, Fov
from frogue.core.ui import MessageLog, Score
from frogue.dungeon.map import WALL

DARK_GRAY = 236
DIM_GRAY = 240


def render(stdscr, world, grid: list[list[str]], depth: int = 1, turns: int = 0) -> None:
    """Draw the grid, then overlay entities on top, then the status line."""
    _init_colors()
    stdscr.clear()
    max_y, max_x = stdscr.getmaxyx()
    visible = world.resources.get(Fov)
    explored = world.resources.get(Explored)
    _draw_grid(stdscr, grid, max_y, max_x, visible, explored)
    _draw_entities(stdscr, world, max_y, max_x, visible, explored)
    _draw_status(stdscr, world, grid, depth, turns, max_y, max_x)
    _draw_messages(stdscr, world, grid, max_y, max_x)
    stdscr.refresh()


def _init_colors() -> None:
    """Initialize the curses color pairs."""
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, -1, -1)
    curses.init_pair(2, -1, DARK_GRAY)
    curses.init_pair(3, DIM_GRAY, -1)


def _draw_grid(stdscr, grid: list[list[str]], max_y: int, max_x: int, visible, explored) -> None:
    """Draw the dungeon cells that are visible or explored."""
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


def _draw_entities(stdscr, world, max_y: int, max_x: int, visible, explored) -> None:
    """Draw the entities that are visible or explored."""
    for _eid, pos, rend in world.query(Position, Renderable):
        if pos.y >= max_y or pos.x >= max_x:
            continue
        state = _cell_state(pos.x, pos.y, visible, explored)
        if state is None:
            continue
        pair = _pair_for(rend.char, state)
        stdscr.addstr(pos.y, pos.x, rend.char, curses.color_pair(pair))


def render_start(stdscr) -> None:
    """Draw the start screen."""
    stdscr.clear()
    _center(stdscr, 0, "FROGUE")
    _center(stdscr, 2, "Press Enter to start a new game")
    _center(stdscr, 3, "Press L to load a save")
    _center(stdscr, 4, "Press Q to quit")
    stdscr.refresh()


def render_dead(stdscr, score: int = 0) -> None:
    """Draw the game-over screen."""
    stdscr.clear()
    _center(stdscr, 0, "YOU DIED.")
    _center(stdscr, 2, f"Score: {score}")
    _center(stdscr, 4, "Press R to restart")
    _center(stdscr, 5, "Press S for the start screen")
    _center(stdscr, 6, "Press Q to quit")
    stdscr.refresh()


def render_win(stdscr, score: int = 0) -> None:
    """Draw the victory screen."""
    stdscr.clear()
    _center(stdscr, 0, "YOU ESCAPED THE DUNGEON.")
    _center(stdscr, 2, f"Score: {score}")
    _center(stdscr, 4, "Press R to restart")
    _center(stdscr, 5, "Press S for the start screen")
    _center(stdscr, 6, "Press Q to quit")
    stdscr.refresh()


def _center(stdscr, y: int, text: str) -> None:
    """Draw text centered horizontally on the given row."""
    _height, width = stdscr.getmaxyx()
    x = max(0, (width - len(text)) // 2)
    stdscr.addstr(y, x, text[:width])


def _draw_status(
    stdscr, world, grid: list[list[str]], depth: int, turns: int, max_y: int, max_x: int
) -> None:
    """Draw the depth, turn counter, and player HP below the map, if it fits."""
    y = len(grid) + 1
    if y >= max_y:
        return
    status = f"Depth: {depth}   Turn: {turns}"
    score = world.resources.get(Score)
    if score is not None:
        status += f"   Score: {score.total(depth, turns)}"
    hp = _player_hp(world)
    if hp is not None:
        status += f"   HP: {hp}"
    stdscr.addstr(y, 0, status[:max_x])


def _draw_messages(stdscr, world, grid: list[list[str]], max_y: int, max_x: int) -> None:
    """Draw the most recent messages below the status line, if they fit."""
    log = world.resources.get(MessageLog)
    if log is None:
        return
    y = len(grid) + 2
    for message in log.messages:
        if y >= max_y:
            return
        stdscr.addstr(y, 0, message[:max_x])
        y += 1


def _player_hp(world) -> str | None:
    """Return the player's HP as 'cur/max', or None if the player is gone."""
    for _eid, _pos, _ctrl in world.query(Position, Controllable):
        life = world.query_single(_eid, Life)
        if life is not None:
            return f"{life.hp}/{life.max_hp}"
    return None


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
