"""Entity and component storage with entity recycling.

Store is the data layer of the ECS - owns entities, components, and queries.
"""

from collections.abc import Iterator
from typing import Any


class Store:
    """Entity and component storage.

    Responsible for:
    - Entity lifecycle (creation, destruction, ID recycling)
    - Component storage and retrieval
    - Entity queries

    This separation allows for future optimizations (archetypes, chunking)
    and serves as middleware for persistence layers.
    """

    # Safety threshold for free ID list to prevent memory bloat
    MAX_FREE_IDS = 10000

    def __init__(self):
        self._next_id = 0
        self._free_ids: list[int] = []
        self._components: dict[type, dict[int, Any]] = {}

    def create_entity(self) -> int:
        """Create a new entity with recycled ID if available.

        Returns:
            New entity ID

        Raises:
            RuntimeError: If entity ID space is exhausted (practically impossible)
        """
        # Use recycled ID if available
        if self._free_ids:
            return self._free_ids.pop()

        # Generate new ID
        eid = self._next_id
        self._next_id += 1

        # Safety check for integer overflow (extremely unlikely in Python)
        if self._next_id < 0:
            raise RuntimeError("Entity ID space exhausted")

        return eid

    def destroy_entity(self, entity: int) -> None:
        """Destroy entity and all its components.

        The entity ID is recycled for future use unless the free list
        has grown too large (memory protection).
        """
        # Remove all components for this entity
        for comp_map in self._components.values():
            comp_map.pop(entity, None)

        # Recycle ID with safety limit to prevent memory bloat
        if len(self._free_ids) < self.MAX_FREE_IDS:
            if entity not in self._free_ids:
                self._free_ids.append(entity)

    def add_component(self, entity: int, component) -> None:
        """Add a component to an entity.

        Overwrites existing component of the same type.
        """
        comp_type = type(component)
        if comp_type not in self._components:
            self._components[comp_type] = {}
        self._components[comp_type][entity] = component

    def get_components(self, component_type: type) -> dict[int, Any]:
        """Get all components of a specific type.

        Returns empty dict if no entities have this component type.
        """
        return self._components.get(component_type, {})

    def has_component(self, entity: int, component_type: type) -> bool:
        """Check if an entity has a specific component."""
        return entity in self._components.get(component_type, {})

    def remove_component(self, entity: int, component_type: type) -> bool:
        """Remove a component from an entity.

        Returns:
            True if component was removed, False if entity didn't have it
        """
        if component_type in self._components:
            if entity in self._components[component_type]:
                del self._components[component_type][entity]
                return True
        return False

    def query_entities(self, *component_types: type) -> Iterator[int]:
        """Yield entity IDs that have all requested component types.

        Deterministic: yields IDs in ascending order.
        Returns empty iterator if no matching entities or if component
        types don't exist (ECS semantics - no error).
        """
        if not component_types:
            return iter(())

        # Get sets of entities for each component type
        sets = []
        for comp_type in component_types:
            comp_map = self._components.get(comp_type, {})
            if not comp_map:  # Empty or missing component type
                return iter(())
            sets.append(set(comp_map.keys()))

        if not sets:
            return iter(())

        # Find intersection (entities with ALL component types)
        ids = set.intersection(*sets)
        for eid in sorted(ids):
            yield eid

    def query(self, *component_types: type) -> Iterator[tuple[int, ...]]:
        """Yield tuples (entity, comp1, comp2, ...) for matching entities.

        Example:
            for eid, pos, vel in store.query(Position, Velocity):
                print(f"Entity {eid} at {pos.x},{pos.y}")
        """
        for eid in self.query_entities(*component_types):
            yield (eid,) + tuple(self._components[t][eid] for t in component_types)

    def query_single(self, eid: int, component_type: type) -> Any | None:
        """Get component for matching entity."""
        return self._components.get(component_type, {}).get(eid)
