"""Tests for save and load via hive world snapshots."""

from frogue.core import FloorCache, Position
from frogue.core.components import Controllable, Life
from frogue.core.fov import Explored
from frogue.core.save import load_game, save_game
from frogue.core.ui import Score


def test_save_load_round_trip(tmp_path) -> None:
    """A saved game should restore depth, turns, HP, and explored cells."""
    path = str(tmp_path / "save.json")
    cache = FloorCache(5, seed=42)
    cache.spawn_player(1)
    player = next(e for e, _, _ in cache.floor(1)["runtime"].world.query(Position, Controllable))
    life = cache.floor(1)["runtime"].world.query_single(player, Life)
    life.hp = 3
    explored = set(cache.floor(1)["runtime"].world.resources.get(Explored).cells)
    save_game(cache, 1, 7, path)

    loaded = load_game(path)
    assert loaded is not None
    assert loaded["depth"] == 1
    assert loaded["turns"] == 7
    player2 = next(
        e for e, _, _ in loaded["cache"].floor(1)["runtime"].world.query(Position, Controllable)
    )
    life2 = loaded["cache"].floor(1)["runtime"].world.query_single(player2, Life)
    assert (life2.hp, life2.max_hp) == (life.hp, life.max_hp)
    explored2 = set(loaded["cache"].floor(1)["runtime"].world.resources.get(Explored).cells)
    assert explored2 == explored


def test_save_load_preserves_shared_score(tmp_path) -> None:
    """Kills should survive a round trip and stay shared across floors."""
    path = str(tmp_path / "save.json")
    cache = FloorCache(5, seed=7)
    cache.spawn_player(1)
    cache.score.kills = 4
    save_game(cache, 1, 0, path)

    loaded = load_game(path)
    assert loaded["cache"].score.kills == 4
    floor1 = loaded["cache"].floor(1)["runtime"].world.resources.get(Score)
    floor5 = loaded["cache"].floor(5)["runtime"].world.resources.get(Score)
    assert floor1 is loaded["cache"].score
    assert floor5 is loaded["cache"].score


def test_load_missing_file_returns_none(tmp_path) -> None:
    """Loading a nonexistent or corrupt file should return None."""
    assert load_game(str(tmp_path / "nope.json")) is None


def test_load_corrupt_schema_returns_none(tmp_path) -> None:
    """A valid JSON file with the wrong schema should return None."""
    bad = tmp_path / "bad.json"
    bad.write_text('{"nope": 1}')
    assert load_game(str(bad)) is None


def test_save_load_without_explicit_seed_matches_grid(tmp_path) -> None:
    """A seeded-at-init game should regenerate the same map after a round trip."""
    path = str(tmp_path / "save.json")
    cache = FloorCache(5)
    cache.spawn_player(1)
    player = next(e for e, _, _ in cache.floor(1)["runtime"].world.query(Position, Controllable))
    pos = cache.floor(1)["runtime"].world.query_single(player, Position)
    grid = cache.floor(1)["grid"]
    save_game(cache, 1, 3, path)

    loaded = load_game(path)
    assert loaded is not None
    loaded_grid = loaded["cache"].floor(1)["grid"]
    assert len(loaded_grid) == len(grid)
    assert all(a == b for a, b in zip(loaded_grid, grid, strict=True))
    player2 = next(
        e for e, _, _ in loaded["cache"].floor(1)["runtime"].world.query(Position, Controllable)
    )
    pos2 = loaded["cache"].floor(1)["runtime"].world.query_single(player2, Position)
    assert (pos2.x, pos2.y) == (pos.x, pos.y)