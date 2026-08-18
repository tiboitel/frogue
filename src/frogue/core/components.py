"""ECS components for frogue."""

from dataclasses import dataclass


@dataclass
class Position:
    """Grid position of an entity."""

    x: int
    y: int


@dataclass
class Renderable:
    """Character used to draw an entity."""

    char: str


@dataclass
class Name:
    """Display name of an entity."""

    name: str


@dataclass
class Controllable:
    """Tag marking an entity as player-controlled."""


@dataclass
class Impassable:
    """Tag marking an entity that blocks movement."""


@dataclass
class Hostile:
    """Tag marking an entity that bump attacks target."""


@dataclass
class Damage:
    """Sides of the damage die rolled on a bump attack."""

    sides: int


@dataclass
class Vision:
    """Radius of the entity's field of view."""

    radius: int = 7


@dataclass
class Stair:
    """A stair linking to another floor."""

    direction: str
    to_depth: int


@dataclass
class Stats:
    """Stat block for an entity."""

    strength: int
    intelligence: int
    dexterity: int


@dataclass
class Life:
    """Hit points for an entity."""

    max_hp: int
    hp: int


@dataclass
class Range:
    """Maximum distance of an entity's ranged attack."""

    distance: int


@dataclass
class Target:
    """Last known player position remembered by a tracking enemy."""

    pos: tuple[int, int] | None = None


@dataclass
class AI:
    """Stateless weighted behavior for a non-player entity."""

    disposition: str
    intents: dict[str, int]
