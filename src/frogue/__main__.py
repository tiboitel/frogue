"""Entry point: generate a dungeon, build the ECS world, and play."""

import curses
from dataclasses import dataclass

from frogue.core import FloorCache, apply_transition
from frogue.core.input import Input
from frogue.core.interact import PendingTransition
from frogue.render import render

MAX_DEPTH = 5


@dataclass
class GameState:
    """Mutable game state shared across the run loop."""

    cache: FloorCache
    depth: int = 1
    turns: int = 0


def main() -> None:
    """Run the game loop until the player quits."""
    state = _new_game()
    curses.wrapper(lambda stdscr: _run(stdscr, state))


def _new_game() -> GameState:
    """Pre-generate every floor and spawn the player on floor 1."""
    cache = FloorCache(MAX_DEPTH)
    cache.spawn_player(1)
    return GameState(cache)


def _run(stdscr, state: GameState) -> None:
    """Render and step the simulation on each keypress."""
    while True:
        floor = state.cache.floor(state.depth)
        render(stdscr, floor["runtime"].world, floor["grid"], state.depth, state.turns)
        key = stdscr.getkey()
        if key in ("q", "KEY_ESCAPE"):
            return
        floor["runtime"].world.resources.get(Input).key = key
        floor["runtime"].step()
        state.turns += 1
        _handle_transition(state)


def _handle_transition(state: GameState) -> None:
    """Apply a pending floor transition if one was requested."""
    floor = state.cache.floor(state.depth)
    pending = floor["runtime"].world.resources.get(PendingTransition)
    new_depth = apply_transition(state.cache, pending, state.depth)
    if new_depth is not None:
        state.depth = new_depth


if __name__ == "__main__":
    main()
