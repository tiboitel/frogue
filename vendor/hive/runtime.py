"""Runtime: simple orchestration for World, Dispatcher and Command Routing."""

import logging

from .command.dispatcher import CommandDispatcher
from .command.router import CommandRouter
from .core import World

logger = logging.getLogger(__name__)


class Runtime:
    """Orchestrate World, Dispatcher and Router."""

    def __init__(self):
        self._world = World()
        self._dispatcher = CommandDispatcher()
        self._router = CommandRouter()
        self.event_bus = self._world.event_bus
        self.steps = 0

    @property
    def world(self) -> World:
        return self._world

    @property
    def resources(self):
        return self._world.resources

    @property
    def router(self) -> CommandRouter:
        return self._router

    @property
    def dispatcher(self) -> CommandDispatcher:
        return self._dispatcher

    @property
    def has_pending(self) -> bool:
        return bool(self._dispatcher.queue)

    def _handle_commands(self, commands) -> int:
        """Process commands with per-command exception handling.

        Returns number of commands routed to a handler.
        """
        processed = 0
        for cmd in commands:
            try:
                routed = self._router.route(cmd, self._world)
            except Exception:
                logger.exception(f"Command handler failed for {type(cmd).__name__}")
            else:
                if routed:
                    processed += 1
        return processed

    def drain(self) -> int:
        """Route pending commands present at drain start toward handlers.

        Only commands that were in the dispatcher when drain() was called are
        processed. Commands emitted by handlers during this call remain in the
        dispatcher's queue and will be processed later.
        """
        commands = self._dispatcher.pop_all()
        if not commands:
            return 0
        return self._handle_commands(commands)

    def step(self) -> None:
        """Execute one simulation step.

        Runs systems, routes commands produced during the step, and increments
        the global `steps` counter.
        """
        self._world.step(self._dispatcher)
        commands = self._dispatcher.pop_all()
        if commands:
            self._handle_commands(commands)
        self.steps += 1

    def step_until_idle(self) -> int:
        """Run steps until there are no pending commands.

        Returns the number of steps executed during this call.
        """
        steps = 0
        while self._dispatcher.queue:
            self.step()
            steps += 1
        return steps
