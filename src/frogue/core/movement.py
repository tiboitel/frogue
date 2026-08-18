"""Movement: commands, collision checks, and the movement system."""

from dataclasses import dataclass

from hive.core import System

from .bump import BumpCommand, bump_handler
from .collision import is_blocked
from .components import Controllable, Position
from .input import GridSize, Input, key_to_delta


@dataclass
class MoveCommand:
    """Request to move an entity by a delta."""

    entity: int
    dx: int
    dy: int


def can_move(world, x: int, y: int) -> bool:
    """Return True if the cell is in bounds and not blocked."""
    size = world.resources.get(GridSize)
    if size is None:
        raise RuntimeError("GridSize resource not registered")
    if not (0 <= x < size.width and 0 <= y < size.height):
        return False
    return not is_blocked(world, x, y)


def move_handler(cmd: MoveCommand, world) -> None:
    """Apply a MoveCommand, or bump into the occupied target cell."""
    pos = world.query_single(cmd.entity, Position)
    if pos is None:
        return
    nx, ny = pos.x + cmd.dx, pos.y + cmd.dy
    if can_move(world, nx, ny):
        pos.x, pos.y = nx, ny
    else:
        bump_handler(BumpCommand(cmd.entity, cmd.dx, cmd.dy), world)


class MovementSystem(System):
    """Resolve a move for the controllable entity on input."""

    def update(self, world, dispatcher) -> None:
        from .ai import Turn

        inp = world.resources.get(Input)
        if inp is None or not inp.key:
            return
        delta = key_to_delta(inp.key)
        if delta is None:
            return
        inp.key = ""
        turn = world.resources.get(Turn)
        if turn is not None:
            turn.acted = True
        for eid, _pos, _ctrl in world.query(Position, Controllable):
            move_handler(MoveCommand(eid, *delta), world)
