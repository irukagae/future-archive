class EventTypes:
    """Constants for all available event types to prevent typos."""
    WINDOW_CHANGED = "WindowChanged"
    HIGH_VELOCITY_TYPING = "HighVelocityTyping"
    BACKSPACE_BURST = "BackspaceBurst"
    IDLE_STARTED = "IdleStarted"
    IDLE_ENDED = "IdleEnded"

    # New Timeline Events
    TIMELINE_STABILITY_CHANGED = "TimelineStabilityChanged"
    TIMELINE_STATE_CHANGED = "TimelineStateChanged"


class EventBus:
    def __init__(self):
        # Dictionary mapping event_type -> list of callback functions
        self._subscribers = {}

    def subscribe(self, event_type, callback):
        """Registers a callback function to listen for a specific event type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        if callback not in self._subscribers[event_type]:
            self._subscribers[event_type].append(callback)

    def unsubscribe(self, event_type, callback):
        """Removes a callback function from an event type."""
        if event_type in self._subscribers:
            if callback in self._subscribers[event_type]:
                self._subscribers[event_type].remove(callback)

    def publish(self, event_type, payload=None):
        """Broadcasts an event and its payload to all registered subscribers."""
        if payload is None:
            payload = {}

        if event_type in self._subscribers:
            for callback in self._subscribers[event_type]:
                callback(event_type, payload)