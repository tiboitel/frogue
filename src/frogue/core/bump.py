"""Bump: attacks when an entity moves into an occupied hostile cell."""

from dataclasses import dataclass
from random import Random

from .components import Controllable, Damage, Hostile, Life, Name, Position
from .ui import GamePhase, MessageLog, Phase, Score

_RNG = Random()


@dataclass
class BumpCommand:
    """Request to bump into the cell at the given delta."""

    entity: int
    dx: int
    dy: int


@dataclass
class Death:
    """Event emitted when an entity's hit points reach zero."""

    entity: int
    attacker: int | None = None


def bump_handler(cmd: BumpCommand, world) -> None:
    """Attack a hostile occupant of the target cell, if any."""
    pos = world.query_single(cmd.entity, Position)
    if pos is None:
        return
    target = _occupant(world, pos.x + cmd.dx, pos.y + cmd.dy)
    if target is None or not _is_hostile(world, target):
        return
    attack(world, cmd.entity, target)


def on_death(event: Death, world, _dispatcher) -> None:
    """Destroy the dead entity, flag game over for the player, or score a kill."""
    if world.has_component(event.entity, Controllable):
        phase = world.resources.get(GamePhase)
        if phase is not None:
            phase.phase = Phase.DEAD
    elif event.attacker is not None and world.has_component(event.attacker, Controllable):
        score = world.resources.get(Score)
        if score is not None:
            score.kills += 1
    world.destroy_entity(event.entity)


def _occupant(world, x: int, y: int) -> int | None:
    """Return the entity occupying the cell, or None."""
    for eid, pos in world.query(Position):
        if pos.x == x and pos.y == y:
            return eid
    return None


def _is_hostile(world, eid: int) -> bool:
    """Return True if the entity is a hostile bump target."""
    return world.has_component(eid, Hostile)


def attack(world, attacker: int, target: int) -> None:
    """Roll the attacker's damage dice against the target's life."""
    damage = world.query_single(attacker, Damage)
    life = world.query_single(target, Life)
    if damage is None or life is None:
        return
    life.hp -= _RNG.randint(1, damage.sides)
    _log_attack(world, attacker, target)
    if life.hp <= 0:
        world.event_bus.emit(Death(target, attacker), world)


def _log_attack(world, attacker: int, target: int) -> None:
    """Append an attack message to the message log, if present."""
    log = world.resources.get(MessageLog)
    if log is None:
        return
    attacker_name = _name(world, attacker)
    target_name = _name(world, target)
    if world.has_component(attacker, Controllable):
        log.add(f"You attack the {target_name}.")
    elif world.has_component(target, Controllable):
        log.add(f"The {attacker_name} attacks you.")
    else:
        log.add(f"The {attacker_name} attacks the {target_name}.")


def _name(world, eid: int) -> str:
    """Return the entity's display name, or a fallback."""
    name = world.query_single(eid, Name)
    return name.name if name is not None else "creature"
