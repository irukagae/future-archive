import time
import random
from src.core.event_bus import EventTypes


class PendingPrediction:
    def __init__(self, expected_event_type, expected_behavior_text, time_window_seconds, confidence,
                 verification_lambda):
        self.id = f"PRD-{random.randint(1000, 9999)}"
        self.expected_event_type = expected_event_type
        self.expected_behavior = expected_behavior_text
        self.creation_time = time.time()
        self.expiry_time = self.creation_time + time_window_seconds
        self.time_window = time_window_seconds
        self.confidence = confidence
        self.status = "Pending"

        # A lambda function that takes the payload of the expected event type
        # and returns True if the specific condition is met.
        self.verification_logic = verification_lambda


class PredictionEngine:
    def __init__(self, event_bus, memory):
        self.event_bus = event_bus
        self.memory = memory
        self.pending_predictions = []

        # Cooldown to prevent prediction spam. (Set short for testing, normally ~1800s)
        self.last_prediction_time = 0
        self.cooldown_seconds = 60

        self._subscribe()

    def _subscribe(self):
        # Listen to all primary events to evaluate heuristics AND resolve active predictions
        events_to_watch = [
            EventTypes.WINDOW_CHANGED,
            EventTypes.HIGH_VELOCITY_TYPING,
            EventTypes.BACKSPACE_BURST,
            EventTypes.IDLE_STARTED,
            EventTypes.IDLE_ENDED
        ]
        for e in events_to_watch:
            self.event_bus.subscribe(e, lambda ev=e, p=None: self._on_event(ev, p))

    def _on_event(self, event_type, payload):
        """Processes an event: first checks if it resolves a prediction, then checks if it sparks a new one."""
        self._check_resolutions(event_type, payload)
        self._evaluate_heuristics(event_type, payload)

    def _check_resolutions(self, event_type, payload):
        """Check if the current event verifies any pending predictions."""
        now = time.time()
        for pred in self.pending_predictions:
            if pred.status == "Pending" and pred.expected_event_type == event_type:
                # Run the lambda logic to see if it matches exactly what we predicted
                if pred.verification_logic(payload):
                    pred.status = "Confirmed"
                    self._publish_result(EventTypes.PREDICTION_VERIFIED, pred)

    def _evaluate_heuristics(self, event_type, payload):
        """Determines if current behavior warrants a new prediction."""
        now = time.time()
        if (now - self.last_prediction_time) < self.cooldown_seconds:
            return

        new_pred = None

        # Heuristic 1: The Frustration Loop
        # If typing fast or deleting rapidly, predict they will seek external help (Browser)
        if event_type in [EventTypes.BACKSPACE_BURST, EventTypes.HIGH_VELOCITY_TYPING]:
            if self.memory.current_sector == "Coding":
                new_pred = PendingPrediction(
                    expected_event_type=EventTypes.WINDOW_CHANGED,
                    expected_behavior_text="Sector Shift to Browser for external knowledge acquisition",
                    time_window_seconds=90,
                    confidence=88,
                    verification_lambda=lambda p: p.get("category", "").lower() == "browser"
                )

        # Heuristic 2: The Fatigue Loop
        # If they've gone idle multiple times, predict they will go idle again soon
        elif event_type == EventTypes.IDLE_ENDED:
            if self.memory.idle_count >= 2:
                new_pred = PendingPrediction(
                    expected_event_type=EventTypes.IDLE_STARTED,
                    expected_behavior_text="Subject will enter another Hibernation State",
                    time_window_seconds=120,
                    confidence=74,
                    verification_lambda=lambda p: True
                )

        # Heuristic 3: The Addictive Loop
        # If they just left a highly visited Media app, predict they will return to it.
        elif event_type == EventTypes.WINDOW_CHANGED:
            prev_app = self.memory.prev_app
            prev_sector = self.memory.prev_sector
            if prev_sector == "Media" and self.memory.get_app_visits(prev_app) >= 2:
                new_pred = PendingPrediction(
                    expected_event_type=EventTypes.WINDOW_CHANGED,
                    expected_behavior_text=f"Return to {prev_app} ({prev_sector} Sector)",
                    time_window_seconds=180,
                    confidence=92,
                    verification_lambda=lambda p: p.get("app_name") == prev_app
                )

        # Register the prediction if one was generated
        if new_pred:
            self.pending_predictions.append(new_pred)
            self.last_prediction_time = now
            self._publish_result(EventTypes.PREDICTION_REGISTERED, new_pred)

    def poll(self):
        """Checks for expired predictions (Averted Destiny). Called by the main loop."""
        now = time.time()
        for pred in self.pending_predictions:
            if pred.status == "Pending" and now > pred.expiry_time:
                pred.status = "Averted"
                self._publish_result(EventTypes.PREDICTION_AVERTED, pred)

    def _publish_result(self, event_type, pred):
        payload = {
            "prediction_id": pred.id,
            "expected_behavior": pred.expected_behavior,
            "confidence": pred.confidence,
            "time_window": pred.time_window
        }
        self.event_bus.publish(event_type, payload)