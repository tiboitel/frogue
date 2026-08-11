"""Tests for floor caching and state preservation across transitions."""

from frogue.core import FloorCache, PendingTransition, Position
from frogue.core.components import Controllable
from frogue.core.fov import Explored
from frogue.core.input import Input


def _descend(cache: FloorCache, depth: int) -> None:
    """Move the player onto the down stair and trigger a transition."""
    floor = cache.floor(depth)
    down = next(s for s in floor["stairs"] if s.direction == "down")
    player = next(e for e, _, _ in floor["runtime"].world.query(Position, Controllable))
    pos = floor["runtime"].world.query_single(player, Position)
    pos.x, pos.y = down.x, down.y
    floor["runtime"].world.resources.get(Input).key = "e"
    floor["runtime"].step()


def _ascend(cache: FloorCache, depth: int) -> None:
    """Move the player onto the up stair and trigger a transition."""
    floor = cache.floor(depth)
    up = next(s for s in floor["stairs"] if s.direction == "up")
    player = next(e for e, _, _ in floor["runtime"].world.query(Position, Controllable))
    pos = floor["runtime"].world.query_single(player, Position)
    pos.x, pos.y = up.x, up.y
    floor["runtime"].world.resources.get(Input).key = "e"
    floor["runtime"].step()


def _pending(cache: FloorCache, depth: int) -> PendingTransition:
    """Return the pending transition resource for a floor."""
    return cache.floor(depth)["runtime"].world.resources.get(PendingTransition)


def _player_pos(cache: FloorCache, depth: int) -> tuple[int, int]:
    """Return the player's position on a floor."""
    floor = cache.floor(depth)
    player = next(e for e, _, _ in floor["runtime"].world.query(Position, Controllable))
    pos = floor["runtime"].world.query_single(player, Position)
    return pos.x, pos.y


def test_descend_requests_transition() -> None:
    """Stepping on the down stair should set a pending transition."""
    cache = FloorCache(5)
    cache.spawn_player(1)
    _descend(cache, 1)
    assert _pending(cache, 1).to_depth == 2


def test_ascend_requests_transition() -> None:
    """Stepping on the up stair should set a pending transition."""
    cache = FloorCache(5)
    cache.spawn_player(1)
    _descend(cache, 1)
    cache.spawn_player(2, arrival=1)
    _ascend(cache, 2)
    assert _pending(cache, 2).to_depth == 1


def test_floor_world_preserved_across_transitions() -> None:
    """Returning to a floor should keep the same world object."""
    cache = FloorCache(5)
    world1 = cache.floor(1)["runtime"].world
    cache.spawn_player(1)
    _descend(cache, 1)
    cache.spawn_player(2, arrival=1)
    _ascend(cache, 2)
    cache.spawn_player(1, arrival=2)
    assert cache.floor(1)["runtime"].world is world1


def test_explored_state_preserved_on_return() -> None:
    """Cells explored before leaving a floor should remain explored."""
    cache = FloorCache(5)
    cache.spawn_player(1)
    world1 = cache.floor(1)["runtime"].world
    explored_before = set(world1.resources.get(Explored).cells)
    _descend(cache, 1)
    cache.spawn_player(2, arrival=1)
    _ascend(cache, 2)
    cache.spawn_player(1, arrival=2)
    explored_after = set(world1.resources.get(Explored).cells)
    assert explored_before <= explored_after


def test_player_spawns_on_arrival_stair() -> None:
    """Descending should place the player on the matching up stair."""
    cache = FloorCache(5)
    cache.spawn_player(1)
    _descend(cache, 1)
    cache.spawn_player(2, arrival=1)
    floor2 = cache.floor(2)
    up = next(s for s in floor2["stairs"] if s.direction == "up")
    assert _player_pos(cache, 2) == (up.x, up.y)


def test_player_spawns_on_down_stair_when_returning() -> None:
    """Ascending back should place the player on the down stair."""
    cache = FloorCache(5)
    cache.spawn_player(1)
    _descend(cache, 1)
    cache.spawn_player(2, arrival=1)
    _ascend(cache, 2)
    cache.spawn_player(1, arrival=2)
    floor1 = cache.floor(1)
    down = next(s for s in floor1["stairs"] if s.direction == "down")
    assert _player_pos(cache, 1) == (down.x, down.y)
