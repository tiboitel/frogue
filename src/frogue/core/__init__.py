"""Core simulation package."""

from .ai import AISystem, Turn
from .collision import is_blocked
from .components import (
    AI,
    Controllable,
    Impassable,
    Life,
    Position,
    Renderable,
    Stair,
    Stats,
    Vision,
)
from .fov import Explored, Fov, VisionSystem, compute_vision, has_line_of_sight
from .input import Grid, Input, is_interact_key, key_to_delta
from .interact import (
    InteractCommand,
    InteractSystem,
    PendingTransition,
    interact_handler,
)
from .level import (
    FloorCache,
    apply_transition,
    build_level,
    build_npcs,
    build_stairs,
    create_game,
    setup_world,
    spawn_player,
)
from .monsters import RAT, Monster, roll_stats
from .movement import MoveCommand, MovementSystem, can_move, move_handler

__all__ = [
    "AI",
    "Controllable",
    "Impassable",
    "Life",
    "Position",
    "Renderable",
    "Stair",
    "Stats",
    "Vision",
    "AISystem",
    "Turn",
    "is_blocked",
    "Explored",
    "Fov",
    "VisionSystem",
    "compute_vision",
    "has_line_of_sight",
    "Grid",
    "Input",
    "is_interact_key",
    "key_to_delta",
    "InteractCommand",
    "InteractSystem",
    "PendingTransition",
    "interact_handler",
    "build_level",
    "build_npcs",
    "build_stairs",
    "create_game",
    "spawn_player",
    "FloorCache",
    "apply_transition",
    "setup_world",
    "RAT",
    "Monster",
    "roll_stats",
    "MovementSystem",
    "MoveCommand",
    "can_move",
    "move_handler",
]
