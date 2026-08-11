import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class EventBus:
    """Synchronous event bus with simple subscribe/unsubscribe."""

    def __init__(self):
        self._subs = defaultdict(list)
        self._next_id = 0

    def on(self, event_type, handler):
        token = (event_type, self._next_id)
        self._next_id += 1
        self._subs[event_type].append((token, handler))
        return token

    def off(self, token):
        event_type, tid = token
        handlers = self._subs.get(event_type, [])
        for i, (t, h) in enumerate(handlers):
            if t == token:
                handlers.pop(i)
                return True
        return False

    def emit(self, event, world=None, dispatcher=None):
        event_type = type(event)
        for _, handler in list(self._subs.get(event_type, [])):
            try:
                handler(event, world, dispatcher)
            except Exception:
                logger.exception(f"Event handler failed for {event_type.__name__}")
