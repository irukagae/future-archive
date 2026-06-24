import time


class TimelineState:
    STABLE = "Stable"
    DIVERGING = "Diverging"
    FRACTURED = "Fractured"
    CRITICAL = "Critical"


class TimelineEngine:
    def __init__(self, event_bus):
        self.event_bus = event_bus

        # Core State
        self.score = 85
        self.baseline = 85
        self.current_state = self._calculate_state(self.score)

        # Session Memory
        self.highest_score = self.score
        self.lowest_score = self.score

        # Drift configuration
        self.last_drift_time = time.time()
        self.drift_interval_seconds = 10.0  # Apply natural drift every 10 seconds

        self._subscribe_to_events()

    def _subscribe_to_events(self):
        # We use a lambda to discard the 'event_type' arg and pass only the payload
        from src.core.event_bus import EventTypes
        self.event_bus.subscribe(EventTypes.WINDOW_CHANGED, lambda e, p: self._on_window_changed(p))
        self.event_bus.subscribe(EventTypes.HIGH_VELOCITY_TYPING, lambda e, p: self._on_high_velocity_typing(p))
        self.event_bus.subscribe(EventTypes.BACKSPACE_BURST, lambda e, p: self._on_backspace_burst(p))
        self.event_bus.subscribe(EventTypes.IDLE_STARTED, lambda e, p: self._on_idle_started(p))
        self.event_bus.subscribe(EventTypes.IDLE_ENDED, lambda e, p: self._on_idle_ended(p))

    def _calculate_state(self, score):
        if score >= 80:
            return TimelineState.STABLE
        elif score >= 50:
            return TimelineState.DIVERGING
        elif score >= 20:
            return TimelineState.FRACTURED
        else:
            return TimelineState.CRITICAL

    def _apply_modifier(self, amount, reason):
        """Core method to alter stability, bounds check, and publish events."""
        if amount == 0:
            return

        previous_score = self.score
        self.score += amount

        # Clamp between 0 and 100
        self.score = max(0, min(100, self.score))

        # Update session extremes
        if self.score > self.highest_score: self.highest_score = self.score
        if self.score < self.lowest_score: self.lowest_score = self.score

        # Only publish if the score actually changed
        if self.score != previous_score:
            from src.core.event_bus import EventTypes
            self.event_bus.publish(EventTypes.TIMELINE_STABILITY_CHANGED, {
                "previous_value": previous_score,
                "new_value": self.score,
                "reason": reason
            })

            # Check for State change
            new_state = self._calculate_state(self.score)
            if new_state != self.current_state:
                previous_state = self.current_state
                self.current_state = new_state

                self.event_bus.publish(EventTypes.TIMELINE_STATE_CHANGED, {
                    "old_state": previous_state,
                    "new_state": self.current_state,
                    "current_stability": self.score
                })

    # --- Event Handlers ---

    def _on_window_changed(self, payload):
        category = payload.get("category", "unknown")

        # Example tuning: Coding is good, Media is bad, everything else is slightly destabilizing
        if category == "coding":
            self._apply_modifier(2, "Sector Shift: Focused Workflow")
        elif category == "media":
            self._apply_modifier(-5, "Sector Shift: Entertainment Distraction")
        else:
            self._apply_modifier(-2, "Sector Shift: Standard")

    def _on_high_velocity_typing(self, payload):
        self._apply_modifier(3, "High Velocity Output")

    def _on_backspace_burst(self, payload):
        self._apply_modifier(-4, "Anomalous Correction Behavior")

    def _on_idle_started(self, payload):
        self._apply_modifier(-5, "Hibernation State Entered")

    def _on_idle_ended(self, payload):
        self._apply_modifier(1, "Activity Resumed")

    # --- Polling Method ---

    def poll(self):
        """Handles natural drift towards the baseline."""
        now = time.time()
        if (now - self.last_drift_time) >= self.drift_interval_seconds:
            self.last_drift_time = now

            if self.score > self.baseline:
                self._apply_modifier(-1, "Natural Drift (Decay)")
            elif self.score < self.baseline:
                self._apply_modifier(1, "Natural Drift (Recovery)")