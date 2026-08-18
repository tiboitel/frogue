"""Archetype stat blocks and stat rolling.

Archetypes are behavior templates, not concrete creatures: any stat block
(later loaded from external config) can instantiate them. The concrete names
(zombie, wraith, ...) belong to config, not to this code.
"""

from dataclasses import dataclass
from random import Random

from .components import Stats


@dataclass(frozen=True)
class Monster:
    """Template describing a monster archetype."""

    name: str
    symbol: str
    disposition: str
    intents: dict[str, int]
    vision: int = 7
    hp_dice: int = 4
    damage: int = 2
    range: int = 3


HUNTER = Monster(
    name="hunter",
    symbol="h",
    disposition="hostile",
    intents={"move_toward_player": 5, "idle": 1},
    vision=6,
    hp_dice=5,
    damage=2,
)

RANGED = Monster(
    name="ranged",
    symbol="r",
    disposition="hostile",
    intents={"shoot": 4, "wander": 1},
    vision=8,
    hp_dice=4,
    damage=2,
    range=5,
)

TRACKER = Monster(
    name="tracker",
    symbol="t",
    disposition="hostile",
    intents={"track": 5, "wander": 1},
    vision=9,
    hp_dice=6,
    damage=2,
)


def roll_stats(rng: Random) -> Stats:
    """Roll a stat block with each stat in the 3-21 range."""
    return Stats(
        strength=rng.randint(3, 21),
        intelligence=rng.randint(3, 21),
        dexterity=rng.randint(3, 21),
    )
