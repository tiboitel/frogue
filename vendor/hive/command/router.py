"""Command routing system for handler registry pattern.

The CommandRouter maps command types to handler functions, enabling
type-safe command processing without isinstance checks.
"""

from collections.abc import Callable
from typing import Any


class CommandRouter:
    """Routes commands to registered handlers based on command type."""

    def __init__(self):
        self._handlers: dict[type, Callable] = {}

    def register(self, cmd_type: type, handler: Callable) -> None:
        """Register a handler for a specific command type.

        Args:
            cmd_type: The command class/type to handle
            handler: Function with signature (cmd, world) -> None

        Raises:
            ValueError: If a handler is already registered for cmd_type
        """
        if cmd_type in self._handlers:
            raise ValueError(f"Handler already registered for {cmd_type}")
        self._handlers[cmd_type] = handler

    def unregister(self, cmd_type: type) -> bool:
        """Remove a handler registration.

        Returns:
            True if handler was removed, False if not found
        """
        if cmd_type in self._handlers:
            del self._handlers[cmd_type]
            return True
        return False

    def route(self, cmd: Any, world) -> bool:
        """Route a single command to its registered handler.

        Args:
            cmd: The command object to route
            world: The World instance to pass to handler

        Returns:
            True if command was routed, False if no handler registered
        """
        cmd_type = type(cmd)
        handler = self._handlers.get(cmd_type)
        if handler:
            handler(cmd, world)
            return True
        return False

    def handle_all(self, commands, world) -> dict[type, int]:
        """Process multiple commands through registered handlers.

        Args:
            commands: Iterable of command objects
            world: The World instance to pass to handlers

        Returns:
            Stats dict mapping {cmd_type: count} for routed commands
        """
        stats = {}
        for cmd in commands:
            cmd_type = type(cmd)
            if self.route(cmd, world):
                stats[cmd_type] = stats.get(cmd_type, 0) + 1
        return stats

    def has_handler(self, cmd_type: type) -> bool:
        """Check if a handler is registered for a command type."""
        return cmd_type in self._handlers

    def registered_types(self):
        """Return list of registered command types."""
        return list(self._handlers.keys())
