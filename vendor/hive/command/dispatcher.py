from collections import deque


class CommandDispatcher:
    """A minimal, generic command queue.

    The framework does not assume any command shape or routing policy — the
    dispatcher simply queues commands for host code or systems to process.
    Host applications can pull commands using `pop_all()` or call `process()`
    with a custom handler.
    """

    def __init__(self):
        self.queue = deque()

    def dispatch(self, command) -> None:
        self.queue.append(command)

    def pop_all(self):
        items = list(self.queue)
        self.queue.clear()
        return items

    def pop(self):
        item = self.queue.popleft()
        return item

    def process(self, handler: callable) -> None:
        """Process all queued commands with `handler(command)`.

        The handler is provided by the host and may dispatch new commands.
        """
        while self.queue:
            cmd = self.queue.popleft()
            handler(cmd)
