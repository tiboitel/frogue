"""Tests for NPC spawning, stats, and AI behavior."""

from random import Random

from hive import Runtime

from frogue.core import (
    AI,
    Life,
    Position,
    Renderable,
    Stats,
    Vision,
    create_game,
    roll_stats,
    spawn_player,
)
from frogue.core.ai import AISystem, Turn
from frogue.core.components import Controllable, Impassable
from frogue.core.input import GridSize
from frogue.core.monsters import RAT
from frogue.core.movement import MoveCommand, move_handler


def _runtime() -> Runtime:
    """A runtime with movement routing and a seeded AI system."""
    runtime = Runtime()
    runtime.world.resources.register(GridSize(30, 30))
    runtime.router.register(MoveCommand, move_handler)
    runtime.world.register(AISystem(seed=0))
    runtime.world.resources.register(Turn())
    return runtime


def _add_player(world, x: int, y: int) -> int:
    """Create a controllable player entity at the given cell."""
    eid = world.create_entity()
    world.add_component(eid, Position(x, y))
    world.add_component(eid, Controllable())
    world.add_component(eid, Impassable())
    return eid


def _add_npc(world, x: int, y: int, intents: dict[str, int] | None = None) -> int:
    """Create an NPC entity with a forced intent set at the given cell."""
    eid = world.create_entity()
    world.add_component(eid, Position(x, y))
    world.add_component(eid, AI("hostile", intents or {"move_toward_player": 1}))
    world.add_component(eid, Vision(radius=7))
    return eid


def test_roll_stats_in_range() -> None:
    """Every stat should land within the 3-21 range."""
    rng = Random(0)
    for _ in range(100):
        stats = roll_stats(rng)
        assert 3 <= stats.strength <= 21
        assert 3 <= stats.intelligence <= 21
        assert 3 <= stats.dexterity <= 21


def test_build_npcs_spawns_depth_scaled_rats() -> None:
    """Rats should spawn at 2*depth across rooms, excluding the player's start."""
    runtime, _grid, rooms, _stairs = create_game(seed=1, depth=2)
    world = runtime.world
    rats = list(world.query(Position, AI, Stats))
    assert len(rats) == 4
    start_room = rooms[0]
    for _eid, pos, ai, stats in rats:
        assert ai.disposition == RAT.disposition
        assert 3 <= stats.strength <= 21
        assert world.has_component(_eid, Impassable)
        assert world.has_component(_eid, Renderable)
        life = world.query_single(_eid, Life)
        assert life is not None
        assert life.hp == life.max_hp == RAT.hp
        assert not (
            start_room.x <= pos.x < start_room.right and start_room.y <= pos.y < start_room.bottom
        )


def test_hostile_seeks_player() -> None:
    """A hostile NPC in line of sight should step toward the player."""
    runtime = _runtime()
    world = runtime.world
    _add_player(world, 10, 10)
    rat = _add_npc(world, 8, 10)
    world.resources.get(Turn).acted = True
    runtime.step()
    pos = world.query_single(rat, Position)
    assert (pos.x, pos.y) == (9, 10)


def test_hostile_idles_out_of_los() -> None:
    """A hostile NPC beyond its vision radius should not move."""
    runtime = _runtime()
    world = runtime.world
    _add_player(world, 10, 10)
    rat = _add_npc(world, 2, 2)
    world.resources.get(Turn).acted = True
    runtime.step()
    pos = world.query_single(rat, Position)
    assert (pos.x, pos.y) == (2, 2)


def test_hostile_stops_adjacent_to_player() -> None:
    """A hostile NPC should not step onto the player's cell."""
    runtime = _runtime()
    world = runtime.world
    _add_player(world, 10, 10)
    rat = _add_npc(world, 9, 10)
    world.add_component(rat, Impassable())
    world.resources.get(Turn).acted = True
    runtime.step()
    pos = world.query_single(rat, Position)
    assert (pos.x, pos.y) == (9, 10)


def test_neutral_wanders() -> None:
    """A neutral NPC with a wander intent should move one random step."""
    runtime = _runtime()
    world = runtime.world
    rat = world.create_entity()
    world.add_component(rat, Position(15, 15))
    world.add_component(rat, AI("neutral", {"wander": 1}))
    world.add_component(rat, Vision(radius=7))
    world.resources.get(Turn).acted = True
    runtime.step()
    pos = world.query_single(rat, Position)
    assert abs(pos.x - 15) + abs(pos.y - 15) == 1


def test_ai_gated_on_player_action() -> None:
    """NPCs should not act when the player did not perform an action."""
    runtime = _runtime()
    world = runtime.world
    _add_player(world, 10, 10)
    rat = _add_npc(world, 8, 10)
    runtime.step()
    pos = world.query_single(rat, Position)
    assert (pos.x, pos.y) == (8, 10)


def test_ai_resets_turn_flag() -> None:
    """The turn flag should be cleared after the AI system runs."""
    runtime = _runtime()
    world = runtime.world
    _add_player(world, 10, 10)
    _add_npc(world, 8, 10)
    world.resources.get(Turn).acted = True
    runtime.step()
    assert world.resources.get(Turn).acted is False


def test_npc_blocks_player_movement() -> None:
    """An impassable NPC should stop the player from entering its cell."""
    runtime = _runtime()
    world = runtime.world
    player = _add_player(world, 10, 10)
    rat = _add_npc(world, 11, 10)
    world.add_component(rat, Impassable())
    move_handler(MoveCommand(player, 1, 0), world)
    pos = world.query_single(player, Position)
    assert (pos.x, pos.y) == (10, 10)


def test_pathfind_routes_around_wall() -> None:
    """A* should find a path around an impassable wall."""
    from frogue.core.ai import _blocked_cells, _pathfind

    runtime = _runtime()
    world = runtime.world
    for x in (9, 10):
        wall = world.create_entity()
        world.add_component(wall, Position(x, 10))
        world.add_component(wall, Impassable())
    path = _pathfind(world, (8, 10), (11, 10), _blocked_cells(world))
    assert path is not None
    assert path[0] == (8, 10)
    assert path[-1] == (11, 10)
    assert (9, 10) not in path
    assert (10, 10) not in path


def test_pathfind_unreachable_returns_none() -> None:
    """A* should return None when the goal is sealed off."""
    from frogue.core.ai import _blocked_cells, _pathfind

    runtime = _runtime()
    world = runtime.world
    for x, y in ((9, 10), (10, 9), (10, 11), (11, 10)):
        wall = world.create_entity()
        world.add_component(wall, Position(x, y))
        world.add_component(wall, Impassable())
    path = _pathfind(world, (8, 10), (10, 10), _blocked_cells(world))
    assert path is None


def test_pathfind_start_equals_goal() -> None:
    """A* should return the start cell when it is the goal."""
    from frogue.core.ai import _blocked_cells, _pathfind

    runtime = _runtime()
    path = _pathfind(runtime.world, (5, 5), (5, 5), _blocked_cells(runtime.world))
    assert path == [(5, 5)]


def test_npcs_block_each_other() -> None:
    """An impassable NPC should stop another NPC from entering its cell."""
    runtime = _runtime()
    world = runtime.world
    _add_player(world, 10, 10)
    rat_a = _add_npc(world, 8, 10)
    rat_b = _add_npc(world, 9, 10)
    world.add_component(rat_a, Impassable())
    world.add_component(rat_b, Impassable())
    for x, y in ((8, 9), (8, 11)):
        wall = world.create_entity()
        world.add_component(wall, Position(x, y))
        world.add_component(wall, Impassable())
    world.resources.get(Turn).acted = True
    runtime.step()
    pos = world.query_single(rat_a, Position)
    assert (pos.x, pos.y) == (8, 10)


def test_spawn_deterministic() -> None:
    """The same seed should spawn rats at the same cells."""
    _runtime_a, _grid_a, _rooms_a, _stairs_a = create_game(seed=7, depth=3)
    _runtime_b, _grid_b, _rooms_b, _stairs_b = create_game(seed=7, depth=3)
    cells_a = {
        (pos.x, pos.y) for _eid, pos, _ai, _stats in _runtime_a.world.query(Position, AI, Stats)
    }
    cells_b = {
        (pos.x, pos.y) for _eid, pos, _ai, _stats in _runtime_b.world.query(Position, AI, Stats)
    }
    assert cells_a == cells_b


def test_no_rats_on_stairs() -> None:
    """Rats should never spawn on a stair cell."""
    runtime, _grid, _rooms, stairs = create_game(seed=1, depth=3)
    stair_cells = {(stair.x, stair.y) for stair in stairs}
    for _eid, pos, _ai, _stats in runtime.world.query(Position, AI, Stats):
        assert (pos.x, pos.y) not in stair_cells


def test_npcs_act_on_interact_key() -> None:
    """NPCs should act when the player presses the interact key."""
    from frogue.core.input import Input
    from frogue.core.level import setup_world

    runtime, _grid, rooms, _stairs = create_game(seed=1, depth=1)
    setup_world(runtime)
    spawn_player(runtime.world, rooms)
    runtime.world.resources.get(Input).key = "e"
    runtime.step()
    assert runtime.world.resources.get(Turn).acted is False


def test_full_pipeline_step_with_npcs() -> None:
    """A full game step should run movement, vision, and AI without error."""
    from frogue.core.input import Input
    from frogue.core.level import setup_world

    runtime, _grid, rooms, _stairs = create_game(seed=1, depth=1)
    setup_world(runtime)
    spawn_player(runtime.world, rooms)
    runtime.world.resources.get(Input).key = "d"
    runtime.step()
    assert runtime.world.resources.get(Turn).acted is False
    assert any(runtime.world.query(Position, AI, Stats))
