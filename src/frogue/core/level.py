"""Build ECS entities from a generated dungeon grid."""

from hive import Runtime

from frogue.dungeon import DOWN, floor_seed
from frogue.dungeon.map import WALL
from frogue.dungeon.rect import Rect
from frogue.dungeon.stair import Stair

from .components import (
    Controllable,
    Impassable,
    Position,
    Renderable,
    Vision,
)
from .components import (
    Stair as StairComponent,
)
from .input import Grid, GridSize


def create_game(
    seed: int | None = None, depth: int = 1, max_depth: int = 5
) -> tuple[Runtime, list[list[str]], list[Rect], list[Stair]]:
    """Build a runtime with walls, grid-size, and stairs from a dungeon."""
    from frogue.dungeon import generate

    runtime = Runtime()
    grid, rooms, stairs = generate(seed=floor_seed(seed, depth), depth=depth, max_depth=max_depth)
    build_level(runtime.world, grid)
    build_stairs(runtime.world, stairs)
    runtime.world.resources.register(GridSize(len(grid[0]), len(grid)))
    runtime.world.resources.register(Grid(grid))
    return runtime, grid, rooms, stairs


def setup_world(runtime: Runtime) -> None:
    """Register systems, handlers, and persistent resources on a runtime."""
    from .fov import Explored, Fov, VisionSystem
    from .input import Input
    from .interact import InteractCommand, InteractSystem, PendingTransition, interact_handler
    from .movement import MoveCommand, MovementSystem, move_handler

    runtime.world.register(MovementSystem())
    runtime.world.register(VisionSystem())
    runtime.world.register(InteractSystem())
    runtime.router.register(MoveCommand, move_handler)
    runtime.router.register(InteractCommand, interact_handler)
    runtime.world.resources.register(Input())
    runtime.world.resources.register(Fov())
    runtime.world.resources.register(Explored())
    runtime.world.resources.register(PendingTransition())


def apply_transition(cache: "FloorCache", pending, current_depth: int) -> int | None:
    """Spawn the player on the target floor and return the new depth."""
    if pending is None or pending.to_depth is None:
        return None
    to_depth = pending.to_depth
    pending.to_depth = None
    cache.spawn_player(to_depth, arrival=current_depth)
    return to_depth


def build_level(world, grid: list[list[str]]) -> None:
    """Create a wall entity for every wall cell in the grid."""
    for y, row in enumerate(grid):
        for x, cell in enumerate(row):
            if cell == WALL:
                eid = world.create_entity()
                world.add_component(eid, Position(x, y))
                world.add_component(eid, Renderable(WALL))
                world.add_component(eid, Impassable())


def build_stairs(world, stairs: list[Stair]) -> None:
    """Create a stair entity for every stair in the floor."""
    for stair in stairs:
        eid = world.create_entity()
        world.add_component(eid, Position(stair.x, stair.y))
        world.add_component(eid, Renderable(_stair_char(stair.direction)))
        world.add_component(eid, StairComponent(stair.direction, stair.to_depth))


def _stair_char(direction: str) -> str:
    """Return the render symbol for a stair direction."""
    return ">" if direction == DOWN else "<"


def spawn_player(world, rooms, index: int = 0) -> int:
    """Create the player entity inside the given room."""
    room = rooms[index]
    eid = world.create_entity()
    world.add_component(eid, Position(room.x + 1, room.y + 1))
    world.add_component(eid, Renderable("@"))
    world.add_component(eid, Controllable())
    world.add_component(eid, Vision())
    return eid


class FloorCache:
    """Pre-generated floors that persist their state across transitions."""

    def __init__(self, max_depth: int, seed: int | None = None) -> None:
        self.max_depth = max_depth
        self.floors = {depth: self._build(depth, seed) for depth in range(1, max_depth + 1)}

    def _build(self, depth: int, seed: int | None) -> dict:
        """Build and set up a single floor's runtime, cached for the session."""
        runtime, grid, rooms, stairs = create_game(seed=seed, depth=depth, max_depth=self.max_depth)
        setup_world(runtime)
        return {"runtime": runtime, "grid": grid, "rooms": rooms, "stairs": stairs}

    def floor(self, depth: int) -> dict:
        """Return the cached floor at the given depth."""
        return self.floors[depth]

    def spawn_player(self, depth: int, arrival: int | None = None) -> int:
        """Place the player on a floor, on the arrival stair if coming from one."""
        floor = self.floors[depth]
        self._destroy_player(floor)
        eid = spawn_player(floor["runtime"].world, floor["rooms"])
        pos = floor["runtime"].world.query_single(eid, Position)
        if arrival is not None:
            stair = self._arrival_stair(floor["stairs"], arrival)
            if stair is not None:
                pos.x, pos.y = stair.x, stair.y
        floor["runtime"].step()
        return eid

    def _destroy_player(self, floor: dict) -> None:
        """Remove any existing player entity from a floor."""
        for eid, _pos, _ctrl in floor["runtime"].world.query(Position, Controllable):
            floor["runtime"].world.destroy_entity(eid)

    def _arrival_stair(self, stairs, from_depth: int):
        """Return the stair on this floor leading back to the previous depth."""
        for stair in stairs:
            if stair.to_depth == from_depth:
                return stair
        return None
