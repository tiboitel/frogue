"""Framework-provided components.

Keep this module intentionally minimal: it defines only a `Destroyed`
marker used by the runtime cleanup. Domain components (position, combat,
AI, etc.) belong in host applications or example projects.
"""

from dataclasses import dataclass


@dataclass
class Destroyed:
    """Marker component indicating an entity should be removed."""

    pass
