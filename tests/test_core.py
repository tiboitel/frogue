"""Tests for the ECS core: level building, player, and movement."""

from frogue.core import (
    Controllable,
    Impassable,
    MoveCommand,
    PendingTransition,
    Position,
    Renderable,
    can_move,
    interact_handler,
    move_handler,
    spawn_player,
)
from frogue.core.interact import InteractCommand
from frogue.core.level import create_game


def _world():
    runtime, grid, rooms, _stairs = create_game(seed=1)
    return runtime, grid, rooms


def test_walls_are_impassable_entities() -> None:
    """Every wall cell should have an Impassable entity."""
    runtime, grid, _rooms = _world()
    walls = {
        (pos.x, pos.y)
        for _eid, pos, _ in runtime.world.query(Position, Impassable)
        if grid[pos.y][pos.x] == "#"
    }
    grid_walls = {(x, y) for y, row in enumerate(grid) for x, cell in enumerate(row) if cell == "#"}
    assert walls == grid_walls


def test_player_spawns_with_components() -> None:
    """Player should have Position, Renderable, and Controllable."""
    runtime, _grid, rooms = _world()
    eid = spawn_player(runtime.world, rooms)
    assert runtime.world.has_component(eid, Position)
    assert runtime.world.has_component(eid, Renderable)
    assert runtime.world.has_component(eid, Controllable)


def test_move_updates_position() -> None:
    """A valid MoveCommand should update the player's position."""
    runtime, _grid, rooms = _world()
    eid = spawn_player(runtime.world, rooms)
    move_handler(MoveCommand(eid, 1, 0), runtime.world)
    pos = runtime.world.query_single(eid, Position)
    room = rooms[0]
    assert (pos.x, pos.y) == (room.x + 2, room.y + 1)


def test_can_move_blocks_void_cells() -> None:
    """Empty (void) cells should not be walkable."""
    runtime, grid, _rooms = _world()
    void = next((x, y) for y, row in enumerate(grid) for x, cell in enumerate(row) if cell == " ")
    assert not can_move(runtime.world, *void)


def test_move_blocked_by_wall() -> None:
    """A MoveCommand into an impassable cell should be ignored."""
    runtime, _grid, rooms = _world()
    eid = spawn_player(runtime.world, rooms)
    # Move left until blocked; position should stabilize.
    for _ in range(50):
        move_handler(MoveCommand(eid, -1, 0), runtime.world)
    pos = runtime.world.query_single(eid, Position)
    before = (pos.x, pos.y)
    move_handler(MoveCommand(eid, -1, 0), runtime.world)
    assert (pos.x, pos.y) == before


def test_can_move_out_of_bounds() -> None:
    """Cells outside the grid should not be walkable."""
    runtime, _grid, rooms = _world()
    eid = spawn_player(runtime.world, rooms)
    pos = runtime.world.query_single(eid, Position)
    assert can_move(runtime.world, pos.x + 1, pos.y)
    assert not can_move(runtime.world, -1, 0)


def test_player_cannot_enter_void() -> None:
    """The player should never move into an empty (void) cell."""
    runtime, grid, rooms = _world()
    eid = spawn_player(runtime.world, rooms)
    void = {(x, y) for y, row in enumerate(grid) for x, cell in enumerate(row) if cell == " "}
    for _ in range(200):
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            move_handler(MoveCommand(eid, dx, dy), runtime.world)
        pos = runtime.world.query_single(eid, Position)
        assert (pos.x, pos.y) not in void


def test_interact_on_stair_sets_transition() -> None:
    """Interacting while standing on a stair should request a floor change."""
    runtime, _grid, rooms, stairs = create_game(seed=1, depth=1, max_depth=5)
    eid = spawn_player(runtime.world, rooms)
    runtime.world.resources.register(PendingTransition())
    stair = stairs[0]
    pos = runtime.world.query_single(eid, Position)
    pos.x, pos.y = stair.x, stair.y
    interact_handler(InteractCommand(eid), runtime.world)
    pending = runtime.world.resources.get(PendingTransition)
    assert pending.to_depth == stair.to_depth


def test_interact_off_stair_does_nothing() -> None:
    """Interacting away from a stair should not request a transition."""
    runtime, _grid, rooms, _stairs = create_game(seed=1, depth=1, max_depth=5)
    eid = spawn_player(runtime.world, rooms)
    runtime.world.resources.register(PendingTransition())
    interact_handler(InteractCommand(eid), runtime.world)
    pending = runtime.world.resources.get(PendingTransition)
    assert pending.to_depth is None


def test_interact_key_not_consumed_by_movement() -> None:
    """The interact key should reach the interact system, not movement."""
    from frogue.core.fov import Explored, Fov, VisionSystem
    from frogue.core.input import Input
    from frogue.core.interact import InteractSystem
    from frogue.core.movement import MovementSystem

    runtime, _grid, rooms, stairs = create_game(seed=1, depth=1, max_depth=5)
    eid = spawn_player(runtime.world, rooms)
    runtime.world.register(MovementSystem())
    runtime.world.register(VisionSystem())
    runtime.world.register(InteractSystem())
    runtime.router.register(MoveCommand, move_handler)
    runtime.router.register(InteractCommand, interact_handler)
    runtime.world.resources.register(Input())
    runtime.world.resources.register(Fov())
    runtime.world.resources.register(Explored())
    runtime.world.resources.register(PendingTransition())
    runtime.step()
    stair = stairs[0]
    pos = runtime.world.query_single(eid, Position)
    pos.x, pos.y = stair.x, stair.y
    runtime.world.resources.get(Input).key = "e"
    runtime.step()
    pending = runtime.world.resources.get(PendingTransition)
    assert pending.to_depth == stair.to_depth


def test_player_spawns_with_life_and_damage() -> None:
    """Player should spawn with 8-12 hp and a 1d4 bump attack."""
    from frogue.core.components import Damage, Hostile, Life

    runtime, _grid, rooms = _world()
    eid = spawn_player(runtime.world, rooms)
    life = runtime.world.query_single(eid, Life)
    damage = runtime.world.query_single(eid, Damage)
    assert 8 <= life.max_hp <= 12
    assert life.hp == life.max_hp
    assert damage.sides == 4
    assert runtime.world.has_component(eid, Hostile)


def test_bump_attacks_hostile_occupant() -> None:
    """Bumping a hostile occupant should damage it and keep the mover put."""
    from frogue.core.bump import BumpCommand, bump_handler
    from frogue.core.components import AI, Hostile, Life

    runtime, _grid, rooms = _world()
    world = runtime.world
    player = spawn_player(world, rooms)
    room = rooms[0]
    rat = world.create_entity()
    world.add_component(rat, Position(room.x + 2, room.y + 1))
    world.add_component(rat, AI("hostile", {"idle": 1}))
    world.add_component(rat, Hostile())
    world.add_component(rat, Life(4, 4))
    bump_handler(BumpCommand(player, 1, 0), world)
    life = world.query_single(rat, Life)
    assert 0 <= life.hp < 4
    pos = world.query_single(player, Position)
    assert (pos.x, pos.y) == (room.x + 1, room.y + 1)


def test_bump_wall_does_no_damage() -> None:
    """Bumping a wall should not damage anything and keep the mover put."""
    from frogue.core.bump import BumpCommand, bump_handler
    from frogue.core.components import Impassable

    runtime, _grid, rooms = _world()
    world = runtime.world
    player = spawn_player(world, rooms)
    room = rooms[0]
    wall = world.create_entity()
    world.add_component(wall, Position(room.x + 2, room.y + 1))
    world.add_component(wall, Impassable())
    bump_handler(BumpCommand(player, 1, 0), world)
    pos = world.query_single(player, Position)
    assert (pos.x, pos.y) == (room.x + 1, room.y + 1)


def test_bump_non_hostile_does_no_damage() -> None:
    """Bumping a non-hostile occupant should not damage it."""
    from frogue.core.bump import BumpCommand, bump_handler
    from frogue.core.components import Life

    runtime, _grid, rooms = _world()
    world = runtime.world
    player = spawn_player(world, rooms)
    room = rooms[0]
    npc = world.create_entity()
    world.add_component(npc, Position(room.x + 2, room.y + 1))
    world.add_component(npc, Life(4, 4))
    bump_handler(BumpCommand(player, 1, 0), world)
    life = world.query_single(npc, Life)
    assert life.hp == 4


def test_bump_death_destroys_entity() -> None:
    """An entity reduced to zero hp should be destroyed via the Death event."""
    from frogue.core.bump import BumpCommand, Death, bump_handler, on_death
    from frogue.core.components import AI, Hostile, Life

    runtime, _grid, rooms = _world()
    world = runtime.world
    world.event_bus.on(Death, on_death)
    player = spawn_player(world, rooms)
    room = rooms[0]
    rat = world.create_entity()
    world.add_component(rat, Position(room.x + 2, room.y + 1))
    world.add_component(rat, AI("hostile", {"idle": 1}))
    world.add_component(rat, Hostile())
    world.add_component(rat, Life(1, 1))
    bump_handler(BumpCommand(player, 1, 0), world)
    assert not world.has_component(rat, Life)


def test_bump_consumes_turn() -> None:
    """Bumping into a hostile should still spend the player's turn."""
    from frogue.core.ai import Turn
    from frogue.core.components import AI, Hostile, Impassable, Life
    from frogue.core.input import Input
    from frogue.core.level import setup_world

    runtime, _grid, rooms, _stairs = create_game(seed=1, depth=1)
    setup_world(runtime)
    spawn_player(runtime.world, rooms)
    room = rooms[0]
    rat = runtime.world.create_entity()
    runtime.world.add_component(rat, Position(room.x + 2, room.y + 1))
    runtime.world.add_component(rat, AI("hostile", {"idle": 1}))
    runtime.world.add_component(rat, Hostile())
    runtime.world.add_component(rat, Impassable())
    runtime.world.add_component(rat, Life(4, 4))
    runtime.world.resources.get(Input).key = "d"
    runtime.step()
    assert runtime.world.resources.get(Turn).acted is False


def test_bump_appends_message() -> None:
    """A bump attack should append a message naming the target."""
    from frogue.core.bump import BumpCommand, bump_handler
    from frogue.core.components import AI, Hostile, Life, Name
    from frogue.core.ui import MessageLog

    runtime, _grid, rooms = _world()
    world = runtime.world
    world.resources.register(MessageLog())
    player = spawn_player(world, rooms)
    room = rooms[0]
    rat = world.create_entity()
    world.add_component(rat, Position(room.x + 2, room.y + 1))
    world.add_component(rat, AI("hostile", {"idle": 1}))
    world.add_component(rat, Hostile())
    world.add_component(rat, Life(4, 4))
    world.add_component(rat, Name("rat"))
    bump_handler(BumpCommand(player, 1, 0), world)
    log = world.resources.get(MessageLog)
    assert log.messages and "rat" in log.messages[-1]


def test_player_death_sets_game_over_phase() -> None:
    """Player death should set the game phase to DEAD."""
    from frogue.core.bump import BumpCommand, Death, bump_handler, on_death
    from frogue.core.components import AI, Damage, Hostile, Life, Name
    from frogue.core.ui import GamePhase, Phase

    runtime, _grid, rooms = _world()
    world = runtime.world
    world.resources.register(GamePhase())
    world.event_bus.on(Death, on_death)
    player = spawn_player(world, rooms)
    room = rooms[0]
    rat = world.create_entity()
    world.add_component(rat, Position(room.x + 2, room.y + 1))
    world.add_component(rat, AI("hostile", {"idle": 1}))
    world.add_component(rat, Hostile())
    world.add_component(rat, Life(4, 4))
    world.add_component(rat, Name("rat"))
    world.add_component(rat, Damage(4))
    player_life = world.query_single(player, Life)
    player_life.hp = 1
    bump_handler(BumpCommand(rat, -1, 0), world)
    assert world.resources.get(GamePhase).phase is Phase.DEAD


def test_score_total_formula() -> None:
    """Score should reward kills and depth and penalize turns."""
    from frogue.core.ui import Score

    score = Score()
    assert score.total(1, 0) == 50
    score.kills = 3
    assert score.total(2, 10) == 3 * 10 + 2 * 50 - 10


def test_npc_death_increments_score() -> None:
    """Killing an NPC should increment the shared score resource."""
    from frogue.core.bump import BumpCommand, Death, bump_handler, on_death
    from frogue.core.components import AI, Hostile, Life
    from frogue.core.ui import Score

    runtime, _grid, rooms = _world()
    world = runtime.world
    world.resources.register(Score())
    world.event_bus.on(Death, on_death)
    player = spawn_player(world, rooms)
    room = rooms[0]
    npc = world.create_entity()
    world.add_component(npc, Position(room.x + 2, room.y + 1))
    world.add_component(npc, AI("hostile", {"idle": 1}))
    world.add_component(npc, Hostile())
    world.add_component(npc, Life(1, 1))
    bump_handler(BumpCommand(player, 1, 0), world)
    assert world.resources.get(Score).kills == 1
