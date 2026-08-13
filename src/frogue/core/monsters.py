"""Monster templates and stat rolling."""

from dataclasses import dataclass
from random import Random

from .components import Stats


@dataclass(frozen=True)
class Monster:
    """Template describing a monster type."""

    name: str
    symbol: str
    disposition: str
    intents: dict[str, int]
    vision: int = 7
    hp: int = 5


RAT = Monster(
    name="rat",
    symbol="R",
    disposition="hostile",
    intents={"move_toward_player": 5, "idle": 1},
    vision=6,
)


def roll_stats(rng: Random) -> Stats:
    """Roll a stat block with each stat in the 3-21 range."""
    return Stats(
        strength=rng.randint(3, 21),
        intelligence=rng.randint(3, 21),
        dexterity=rng.randint(3, 21),
    )
