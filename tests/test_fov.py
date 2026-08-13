"""Tests for field of view and line of sight."""

from frogue.core import (
    Explored,
    Fov,
    Position,
    VisionSystem,
    compute_vision,
    has_line_of_sight,
    spawn_player,
)
from frogue.core.input import GridSize
from frogue.core.level import create_game


def _world():
    runtime, grid, rooms, _stairs = create_game(seed=1)
    eid = spawn_player(runtime.world, rooms)
    return runtime, grid, rooms, eid


def _open_world():
    """A runtime with an empty grid so line of sight is never blocked."""
    from hive import Runtime

    runtime = Runtime()
    runtime.world.resources.register(GridSize(30, 30))
    eid = runtime.world.create_entity()
    runtime.world.add_component(eid, Position(15, 15))
    return runtime, eid


def test_line_of_sight_blocked_by_wall() -> None:
    """A wall between two points should block line of sight."""
    from frogue.core.components import Impassable

    runtime, _eid = _open_world()
    runtime.world.create_entity()
    wall = runtime.world.create_entity()
    runtime.world.add_component(wall, Position(7, 5))
    runtime.world.add_component(wall, Impassable())
    assert has_line_of_sight(runtime.world, 5, 5, 6, 5)
    assert not has_line_of_sight(runtime.world, 5, 5, 9, 5)


def test_line_of_sight_ignores_observer() -> None:
    """An impassable entity at the observer's cell should not block LOS."""
    from frogue.core.components import Impassable

    runtime, _eid = _open_world()
    observer = runtime.world.create_entity()
    runtime.world.add_component(observer, Position(5, 5))
    runtime.world.add_component(observer, Impassable())
    assert has_line_of_sight(runtime.world, 5, 5, 9, 5)


def test_compute_vision_in_bounds() -> None:
    """Vision should only include in-bounds cells."""
    runtime, _grid, _rooms, eid = _world()
    pos = runtime.world.query_single(eid, Position)
    visible = compute_vision(runtime.world, pos.x, pos.y, 8)
    size = runtime.world.resources.get(GridSize)
    for x, y in visible:
        assert 0 <= x < size.width
        assert 0 <= y < size.height


def test_vision_system_updates_resources() -> None:
    """VisionSystem should populate Fov and Explored resources."""
    runtime, _grid, _rooms, eid = _world()
    runtime.world.resources.register(Fov())
    runtime.world.resources.register(Explored())
    VisionSystem().update(runtime.world, None)
    fov = runtime.world.resources.get(Fov)
    explored = runtime.world.resources.get(Explored)
    pos = runtime.world.query_single(eid, Position)
    assert (pos.x, pos.y) in fov.cells
    assert (pos.x, pos.y) in explored.cells
    assert explored.cells >= fov.cells


def test_vision_is_360_degrees() -> None:
    """Vision should not depend on facing; behind cells are visible."""
    runtime, eid = _open_world()
    pos = runtime.world.query_single(eid, Position)
    px, py = pos.x, pos.y
    visible = compute_vision(runtime.world, px, py, 8)
    assert (px + 5, py) in visible
    assert (px - 5, py) in visible
    assert (px, py + 5) in visible
    assert (px, py - 5) in visible


def test_vision_radius_reduced() -> None:
    """Default radius 7 should hide cells at distance 8."""
    runtime, eid = _open_world()
    pos = runtime.world.query_single(eid, Position)
    px, py = pos.x, pos.y
    visible = compute_vision(runtime.world, px, py, 7)
    assert (px + 7, py) in visible
    assert (px + 8, py) not in visible
