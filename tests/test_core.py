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
    walls = {(pos.x, pos.y) for _eid, pos, _ in runtime.world.query(Position, Impassable)}
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
    assert can_move(runtime.world, pos.x, pos.y)
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
