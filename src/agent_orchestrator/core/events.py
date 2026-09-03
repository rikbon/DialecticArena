"""
Event bus and lifecycle hooks for the agent orchestrator.
Allows decoupling the execution engine from console reporting, telemetry, and webhooks.
"""

from typing import Callable, Optional
from agent_orchestrator.types import ArenaEvent, EventType

EventHandler = Callable[[ArenaEvent], None]


class EventBus:
    """Publish-subscribe event bus for arena lifecycle events."""

    def __init__(self):
        self._listeners: dict[Optional[EventType], list[EventHandler]] = {}

    def subscribe(self, handler: EventHandler, event_type: Optional[EventType] = None) -> None:
        """Register a handler for a specific event type, or all events if event_type is None."""
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(handler)

    def dispatch(self, event: ArenaEvent) -> None:
        """Dispatch an event to all interested handlers."""
        # Specific handlers
        handlers = list(self._listeners.get(event.event_type, []))
        # Global handlers
        handlers.extend(self._listeners.get(None, []))

        for handler in handlers:
            try:
                handler(event)
            except Exception:
                # Observers must never crash the main debate loop
                pass
