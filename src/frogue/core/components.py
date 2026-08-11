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
class Controllable:
    """Tag marking an entity as player-controlled."""


@dataclass
class Impassable:
    """Tag marking an entity that blocks movement."""


@dataclass
class Vision:
    """Radius of the entity's field of view."""

    radius: int = 7


@dataclass
class Stair:
    """A stair linking to another floor."""

    direction: str
    to_depth: int
