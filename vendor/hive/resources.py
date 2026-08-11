from typing import TypeVar

T = TypeVar("T")


class ResourceRegistry:
    """Lightweight resource storage for global/shared objects."""

    def __init__(self):
        self._data = {}

    def register(self, resource: T) -> None:
        """Register resource using its type as key."""
        key = type(resource)
        self._data[key] = resource

    def get(self, resource_type: type[T]) -> T | None:
        """Get resource by type. None if not found."""
        if resource_type not in self._data:
            return None
        return self._data[resource_type]

    def get_or(self, resource_type: type[T], default: T) -> T:
        """Get resource by type with default fallback."""
        return self._data.get(resource_type, default)

    def has(self, resource_type: type[T]) -> bool:
        return resource_type in self._data

    def all(self):
        return dict(self._data)
