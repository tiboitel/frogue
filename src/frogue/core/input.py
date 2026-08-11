"""Input handling: map keys to movement deltas."""

from dataclasses import dataclass

KEYMAP = {
    "w": (0, -1),
    "s": (0, 1),
    "a": (-1, 0),
    "d": (1, 0),
}

INTERACT_KEY = "e"


@dataclass
class Input:
    """Resource holding the most recent key pressed."""

    key: str = ""


@dataclass
class GridSize:
    """Resource holding the dungeon grid dimensions."""

    width: int
    height: int


@dataclass
class Grid:
    """Resource holding the dungeon grid cells."""

    cells: list[list[str]]


def key_to_delta(key: str) -> tuple[int, int] | None:
    """Return the movement delta for a key, or None if not a movement key."""
    return KEYMAP.get(key)


def is_interact_key(key: str) -> bool:
    """Return True if the key triggers interaction."""
    return key == INTERACT_KEY
