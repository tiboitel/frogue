"""UI resources: game phase and message log."""

from dataclasses import dataclass, field
from enum import Enum


class Phase(Enum):
    """Top-level game screen."""

    START = "start"
    PLAYING = "playing"
    DEAD = "dead"
    WIN = "win"


@dataclass
class GamePhase:
    """Resource holding the current game screen."""

    phase: Phase = Phase.START


@dataclass
class MessageLog:
    """Resource holding the most recent game messages."""

    messages: list[str] = field(default_factory=list)
    max_messages: int = 4

    def add(self, message: str) -> None:
        """Append a message, dropping the oldest beyond the cap."""
        self.messages.append(message)
        del self.messages[: -self.max_messages]


@dataclass
class Score:
    """Resource tracking the player's kills across floors."""

    kills: int = 0

    def total(self, depth: int, turns: int) -> int:
        """Return the final score: kills, depth bonus, and turn penalty."""
        return max(0, self.kills * 10 + depth * 50 - turns)
