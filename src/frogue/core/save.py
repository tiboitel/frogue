"""Save and load the game via hive world snapshots."""

import json
from pathlib import Path

from hive import Runtime
from hive.serialize import load_into_world, register_serializer

from frogue.dungeon import floor_seed, generate

from .components import Stair, Target
from .fov import Explored, Fov
from .level import FloorCache, setup_world
from .ui import GamePhase, Phase, Score


def _fov_to_dict(fov: Fov) -> dict:
    """Serialize a Fov resource as a sorted cell list."""
    return {"cells": sorted(fov.cells)}


def _fov_from_dict(data: dict) -> Fov:
    """Rebuild a Fov resource from a cell list."""
    return Fov({tuple(cell) for cell in data["cells"]})


def _explored_to_dict(explored: Explored) -> dict:
    """Serialize an Explored resource as a sorted cell list."""
    return {"cells": sorted(explored.cells)}


def _explored_from_dict(data: dict) -> Explored:
    """Rebuild an Explored resource from a cell list."""
    return Explored({tuple(cell) for cell in data["cells"]})


def _phase_to_dict(phase: GamePhase) -> dict:
    """Serialize a GamePhase resource by its enum value."""
    return {"phase": phase.phase.value}


def _phase_from_dict(data: dict) -> GamePhase:
    """Rebuild a GamePhase resource from an enum value."""
    return GamePhase(Phase(data["phase"]))


def _target_to_dict(target: Target) -> dict:
    """Serialize a Target component, normalizing the position to a list."""
    return {"pos": list(target.pos) if target.pos is not None else None}


def _target_from_dict(data: dict) -> Target:
    """Rebuild a Target component, normalizing the position to a tuple."""
    return Target(tuple(data["pos"]) if data["pos"] is not None else None)


def _stair_to_dict(stair: Stair) -> dict:
    """Serialize a Stair component by its fields."""
    return {"direction": stair.direction, "to_depth": stair.to_depth}


def _stair_from_dict(data: dict) -> Stair:
    """Rebuild a Stair component from its fields."""
    return Stair(data["direction"], data["to_depth"])


def _register_serializers() -> None:
    """Register the custom serializers for non-JSON-safe resources."""
    register_serializer(Fov, _fov_to_dict, _fov_from_dict)
    register_serializer(Explored, _explored_to_dict, _explored_from_dict)
    register_serializer(GamePhase, _phase_to_dict, _phase_from_dict)
    register_serializer(Target, _target_to_dict, _target_from_dict)
    register_serializer(Stair, _stair_to_dict, _stair_from_dict)


def save_game(cache: FloorCache, depth: int, turns: int, path: str) -> None:
    """Write every floor's snapshot and the game state to a JSON file."""
    _register_serializers()
    payload = {
        "max_depth": cache.max_depth,
        "seed": cache.seed,
        "depth": depth,
        "turns": turns,
        "score_kills": cache.score.kills,
        "floors": {
            str(d): cache.floor(d)["runtime"].world.snapshot()
            for d in range(1, cache.max_depth + 1)
        },
    }
    Path(path).write_text(json.dumps(payload))


def load_game(path: str) -> dict | None:
    """Restore a game from a JSON file, returning cache, depth, and turns."""
    try:
        payload = json.loads(Path(path).read_text())
        _register_serializers()
        seed = payload.get("seed")
        floors = {
            int(depth_str): _load_floor(snapshot, payload["max_depth"], seed, depth_str)
            for depth_str, snapshot in payload["floors"].items()
        }
        cache = FloorCache(payload["max_depth"], seed=seed, floors=floors)
        for depth in range(1, payload["max_depth"] + 1):
            cache.floor(depth)["runtime"].world.resources.register(cache.score)
        cache.score.kills = payload["score_kills"]
        return {"cache": cache, "depth": payload["depth"], "turns": payload["turns"]}
    except (OSError, ValueError, KeyError, TypeError, AttributeError, ImportError):
        return None


def _load_floor(snapshot: dict, max_depth: int, seed: int | None, depth_str: str) -> dict:
    """Rebuild a floor's runtime from its snapshot, reusing the deterministic layout."""
    depth = int(depth_str)
    grid, rooms, stairs = generate(seed=floor_seed(seed, depth), depth=depth, max_depth=max_depth)
    runtime = Runtime()
    setup_world(runtime, Score())
    load_into_world(snapshot, runtime.world)
    return {"runtime": runtime, "grid": grid, "rooms": rooms, "stairs": stairs}