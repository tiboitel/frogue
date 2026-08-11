"""Core ECS: World, System, and entity/component management.

World orchestrates the simulation. Store owns the data.
"""

from collections.abc import Iterator
from typing import Any

from .events import EventBus
from .resources import ResourceRegistry
from .serialize import snapshot as _snapshot
from .store import Store


class System:
    """Base class for ECS systems.

    Systems implement game logic by processing entities with specific components.
    """

    def update(self, world: "World", dispatcher) -> None:
        """Execute system logic.

        Args:
            world: The World instance (access store via world.store)
            dispatcher: CommandDispatcher for emitting commands
        """
        raise NotImplementedError


class World:
    """Simulation container: owns Store, systems, event_bus, and resources.

    World is the simulation. Store owns the simulation data (entities, components).
    Resources hold static data (config, assets).
    """

    def __init__(self):
        self._store = Store()
        self._systems: list[tuple[int, object]] = []
        self.event_bus = EventBus()
        self.resources = ResourceRegistry()

    @property
    def store(self) -> Store:
        """Access the entity/component store."""
        return self._store

    # Convenience methods that delegate to store
    def create_entity(self) -> int:
        """Create a new entity."""
        return self._store.create_entity()

    def destroy_entity(self, entity: int) -> None:
        """Destroy an entity and all its components."""
        self._store.destroy_entity(entity)

    def add_component(self, entity: int, component) -> None:
        """Add a component to an entity."""
        self._store.add_component(entity, component)

    def get_components(self, component_type: type) -> dict[int, Any]:
        """Get all components of a specific type."""
        return self._store.get_components(component_type)

    def has_component(self, entity: int, component_type: type) -> bool:
        """Check if an entity has a specific component."""
        return self._store.has_component(entity, component_type)

    def remove_component(self, entity: int, component_type: type) -> bool:
        """Remove a component from an entity."""
        return self._store.remove_component(entity, component_type)

    def query_entities(self, *component_types: type) -> Iterator[int]:
        """Query entity IDs with all component types."""
        return self._store.query_entities(*component_types)

    def query(self, *component_types: type) -> Iterator[tuple[int, ...]]:
        """Query entities with all component types.

        Yields tuples: (entity_id, component1, component2, ...)
        """
        return self._store.query(*component_types)

    def query_single(self, eid: int, component_type: type) -> Any | None:
        """Query a component with matching entity id."""

        return self._store.query_single(eid, component_type)

    # System management
    def register(self, system, priority: int = 0) -> None:
        """Register a system with optional priority (lower = earlier)."""
        self._systems.append((priority, system))
        self._systems.sort(key=lambda t: t[0])

    def step(self, dispatcher=None) -> None:
        """Execute one simulation step.

        Runs all systems in priority order, passing world and dispatcher.
        """
        for _, system in list(self._systems):
            system.update(self, dispatcher)

    def snapshot(self):
        """Create a serializable snapshot of the world state."""
        return _snapshot(self)
