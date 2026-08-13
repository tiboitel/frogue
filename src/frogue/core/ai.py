"""AI: turn tracking and weighted stateless behaviors for NPCs."""

import heapq
from dataclasses import dataclass
from random import Random

from hive.core import System

from frogue.dungeon.map import EMPTY

from .components import AI, Controllable, Impassable, Position, Vision
from .fov import has_line_of_sight
from .input import Grid, GridSize
from .movement import MoveCommand, can_move

DIRECTIONS = ((1, 0), (-1, 0), (0, 1), (0, -1))


@dataclass
class Turn:
    """Resource tracking whether the player acted this step."""

    acted: bool = False


class AISystem(System):
    """Pick a weighted intent for each NPC and dispatch its move."""

    def __init__(self, seed: int | None = None) -> None:
        self.rng = Random(seed)

    def update(self, world, dispatcher) -> None:
        turn = world.resources.get(Turn)
        if turn is None or not turn.acted:
            return
        player = _player_pos(world)
        blocked = _blocked_cells(world)
        for eid, pos, ai, vision in world.query(Position, AI, Vision):
            intent = _pick_intent(self.rng, ai.intents)
            _run_intent(world, dispatcher, eid, pos, vision, player, intent, self.rng, blocked)
        turn.acted = False


def _player_pos(world) -> tuple[int, int] | None:
    """Return the player's position, or None if no player is present."""
    for _eid, pos, _ctrl in world.query(Position, Controllable):
        return pos.x, pos.y
    return None


def _blocked_cells(world) -> set[tuple[int, int]]:
    """Return all cells blocked by impassable entities or void."""
    cells = {(pos.x, pos.y) for _eid, pos, _ in world.query(Position, Impassable)}
    grid = world.resources.get(Grid)
    if grid is not None:
        cells |= {
            (x, y)
            for y, row in enumerate(grid.cells)
            for x, cell in enumerate(row)
            if cell == EMPTY
        }
    return cells


def _pick_intent(rng: Random, intents: dict[str, int]) -> str:
    """Return an intent name chosen by weight."""
    if not intents:
        return "idle"
    total = sum(intents.values())
    if total <= 0:
        return next(iter(intents))
    roll = rng.randrange(total)
    for name, weight in intents.items():
        roll -= weight
        if roll < 0:
            return name
    return next(iter(intents))


def _run_intent(world, dispatcher, eid, pos, vision, player, intent, rng, blocked) -> None:
    """Execute the intent's pre-coded action, if any."""
    action = _ACTIONS.get(intent)
    if action is not None:
        action(world, dispatcher, eid, pos, vision, player, rng, blocked)


def _move_toward_player(world, dispatcher, eid, pos, vision, player, _rng, blocked) -> None:
    """Step toward the player when they are in line of sight."""
    if player is None:
        return
    px, py = player
    if abs(pos.x - px) + abs(pos.y - py) > vision.radius:
        return
    if not has_line_of_sight(world, pos.x, pos.y, px, py):
        return
    _step_toward(world, dispatcher, eid, pos.x, pos.y, px, py, blocked)


def _wander(world, dispatcher, eid, pos, _vision, _player, rng, _blocked) -> None:
    """Step in a random walkable direction."""
    dx, dy = rng.choice(DIRECTIONS)
    if can_move(world, pos.x + dx, pos.y + dy):
        dispatcher.dispatch(MoveCommand(eid, dx, dy))


def _step_toward(world, dispatcher, eid, x, y, tx, ty, blocked) -> None:
    """Dispatch the first step of an A* path toward the target."""
    path = _pathfind(world, (x, y), (tx, ty), blocked)
    if path is None or len(path) < 2:
        return
    nx, ny = path[1]
    dispatcher.dispatch(MoveCommand(eid, nx - x, ny - y))


def _pathfind(
    world, start: tuple[int, int], goal: tuple[int, int], blocked: set[tuple[int, int]]
) -> list[tuple[int, int]] | None:
    """Return a 4-way path from start to goal, or None if unreachable.

    The goal cell is always treated as walkable so the path can end on an
    occupied target; the final step is rejected by the move handler.
    """
    if start == goal:
        return [start]
    size = world.resources.get(GridSize)
    open_set = [(0, start)]
    came_from: dict[tuple[int, int], tuple[int, int]] = {}
    g_score: dict[tuple[int, int], int] = {start: 0}
    while open_set:
        _f, current = heapq.heappop(open_set)
        if current == goal:
            return _reconstruct_path(came_from, current)
        for dx, dy in DIRECTIONS:
            neighbor = (current[0] + dx, current[1] + dy)
            if size is not None and not (
                0 <= neighbor[0] < size.width and 0 <= neighbor[1] < size.height
            ):
                continue
            if neighbor != goal and neighbor in blocked:
                continue
            tentative = g_score[current] + 1
            if tentative < g_score.get(neighbor, float("inf")):
                came_from[neighbor] = current
                g_score[neighbor] = tentative
                heapq.heappush(open_set, (tentative + _manhattan(neighbor, goal), neighbor))
    return None


def _reconstruct_path(came_from, current: tuple[int, int]) -> list[tuple[int, int]]:
    """Rebuild the path from start to current using the came_from map."""
    path = [current]
    while current in came_from:
        current = came_from[current]
        path.append(current)
    path.reverse()
    return path


def _manhattan(a: tuple[int, int], b: tuple[int, int]) -> int:
    """Return the Manhattan distance between two cells."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


_ACTIONS = {
    "move_toward_player": _move_toward_player,
    "wander": _wander,
}
