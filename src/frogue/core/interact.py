"""Interaction: commands and systems for interacting with entities."""

from dataclasses import dataclass

from hive.core import System

from .components import Controllable, Position, Stair
from .input import Input, is_interact_key


@dataclass
class InteractCommand:
    """Request to interact with the entity under the player."""

    entity: int


@dataclass
class PendingTransition:
    """Resource signalling a pending floor change."""

    to_depth: int | None = None


def interact_handler(cmd: InteractCommand, world) -> None:
    """Trigger a floor transition if the player stands on a stair."""
    pos = world.query_single(cmd.entity, Position)
    if pos is None:
        return
    for _eid, stair_pos, stair in world.query(Position, Stair):
        if stair_pos.x == pos.x and stair_pos.y == pos.y:
            pending = world.resources.get(PendingTransition)
            if pending is not None:
                pending.to_depth = stair.to_depth
            return


class InteractSystem(System):
    """Dispatch an InteractCommand for the controllable entity on input."""

    def update(self, world, dispatcher) -> None:
        inp = world.resources.get(Input)
        if inp is None or not is_interact_key(inp.key):
            return
        inp.key = ""
        for eid, _pos, _ctrl in world.query(Position, Controllable):
            dispatcher.dispatch(InteractCommand(eid))
