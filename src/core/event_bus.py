class EventTypes:
    WINDOW_CHANGED = "WindowChanged"
    HIGH_VELOCITY_TYPING = "HighVelocityTyping"
    BACKSPACE_BURST = "BackspaceBurst"
    IDLE_STARTED = "IdleStarted"
    IDLE_ENDED = "IdleEnded"

    TIMELINE_STABILITY_CHANGED = "TimelineStabilityChanged"
    TIMELINE_STATE_CHANGED = "TimelineStateChanged"

    # New Prediction Events
    PREDICTION_REGISTERED = "PredictionRegistered"
    PREDICTION_VERIFIED = "PredictionVerified"
    PREDICTION_AVERTED = "PredictionAverted"


class EventBus:
    def __init__(self):
        self._subscribers = {}

    def subscribe(self, event_type, callback):
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        if callback not in self._subscribers[event_type]:
            self._subscribers[event_type].append(callback)

    def unsubscribe(self, event_type, callback):
        if event_type in self._subscribers:
            if callback in self._subscribers[event_type]:
                self._subscribers[event_type].remove(callback)

    def publish(self, event_type, payload=None):
        if payload is None:
            payload = {}
        if event_type in self._subscribers:
            for callback in self._subscribers[event_type]:
                callback(event_type, payload)