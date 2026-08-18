"""Entry point: start screen, game loop, and game-over screen."""

import curses
from dataclasses import dataclass

from frogue.core import FloorCache, apply_transition
from frogue.core.input import Input
from frogue.core.interact import PendingTransition
from frogue.core.save import load_game, save_game
from frogue.core.ui import GamePhase, Phase
from frogue.render import render, render_dead, render_start, render_win

MAX_DEPTH = 5
SAVE_PATH = "save.json"


@dataclass
class GameState:
    """Mutable game state shared across the run loop."""

    cache: FloorCache | None = None
    depth: int = 1
    turns: int = 0


def main() -> None:
    """Run the game loop until the player quits."""
    curses.wrapper(_run)


def _run(stdscr) -> None:
    """Dispatch between the start, playing, and game-over screens."""
    state = GameState()
    while True:
        if state.cache is None:
            if _start_screen(stdscr, state):
                return
        elif _is_dead(state):
            if _dead_screen(stdscr, state):
                return
        elif _is_win(state):
            if _win_screen(stdscr, state):
                return
        elif _play_turn(stdscr, state):
            return


def _start_screen(stdscr, state: GameState) -> bool:
    """Show the start screen; return True when the player quits."""
    render_start(stdscr)
    key = stdscr.getkey()
    if key in ("q", "Q", "KEY_ESCAPE"):
        return True
    if key in ("\n", "\r", "KEY_ENTER"):
        _new_game(state)
    elif key in ("l", "L"):
        loaded = load_game(SAVE_PATH)
        if loaded is not None:
            state.cache = loaded["cache"]
            state.depth = loaded["depth"]
            state.turns = loaded["turns"]
    return False


def _dead_screen(stdscr, state: GameState) -> bool:
    """Show the game-over screen; return True when the player quits."""
    render_dead(stdscr, _score(state))
    key = stdscr.getkey()
    if key in ("q", "Q", "KEY_ESCAPE"):
        return True
    if key in ("r", "R"):
        _new_game(state)
    elif key in ("s", "S"):
        state.cache = None
    return False


def _win_screen(stdscr, state: GameState) -> bool:
    """Show the victory screen; return True when the player quits."""
    render_win(stdscr, _score(state))
    key = stdscr.getkey()
    if key in ("q", "Q", "KEY_ESCAPE"):
        return True
    if key in ("r", "R"):
        _new_game(state)
    elif key in ("s", "S"):
        state.cache = None
    return False


def _play_turn(stdscr, state: GameState) -> bool:
    """Render and step one turn; return True when the player quits."""
    floor = state.cache.floor(state.depth)
    render(stdscr, floor["runtime"].world, floor["grid"], state.depth, state.turns)
    key = stdscr.getkey()
    if key in ("q", "KEY_ESCAPE"):
        return True
    if key == "S":
        save_game(state.cache, state.depth, state.turns, SAVE_PATH)
        return False
    floor["runtime"].world.resources.get(Input).key = key
    floor["runtime"].step()
    state.turns += 1
    _handle_transition(state)
    return False


def _new_game(state: GameState) -> None:
    """Rebuild every floor and spawn the player on floor 1."""
    state.cache = FloorCache(MAX_DEPTH)
    state.depth = 1
    state.turns = 0
    state.cache.spawn_player(1)


def _is_dead(state: GameState) -> bool:
    """Return True when the current floor's game phase is DEAD."""
    floor = state.cache.floor(state.depth)
    phase = floor["runtime"].world.resources.get(GamePhase)
    return phase is not None and phase.phase is Phase.DEAD


def _is_win(state: GameState) -> bool:
    """Return True when the current floor's game phase is WIN."""
    floor = state.cache.floor(state.depth)
    phase = floor["runtime"].world.resources.get(GamePhase)
    return phase is not None and phase.phase is Phase.WIN


def _score(state: GameState) -> int:
    """Return the current total score."""
    return state.cache.score.total(state.depth, state.turns)


def _handle_transition(state: GameState) -> None:
    """Apply a pending floor transition if one was requested."""
    floor = state.cache.floor(state.depth)
    pending = floor["runtime"].world.resources.get(PendingTransition)
    new_depth = apply_transition(state.cache, pending, state.depth)
    if new_depth is not None:
        state.depth = new_depth


if __name__ == "__main__":
    main()
