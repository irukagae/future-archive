import time
from collections import deque, defaultdict
from src.core.event_bus import EventTypes


class TemporalMemory:
    def __init__(self, event_bus):
        self.event_bus = event_bus

        # Session Time Tracking
        self.session_start = time.time()

        # Location Context
        self.current_app = "System"
        self.current_sector = "General"
        self.prev_app = "System"
        self.prev_sector = "General"

        # Rolling Narrative Memory
        self.recent_events = deque(maxlen=10)

        # Session Statistics
        self.app_visits = defaultdict(int)
        self.sector_visits = defaultdict(int)
        self.transition_count = 0
        self.idle_count = 0
        self.longest_idle = 0.0
        self.highest_stability = 85
        self.lowest_stability = 85

        self._subscribe()

    def _subscribe(self):
        # FIXED: Absorb the event_type using lambda e, p:
        self.event_bus.subscribe(EventTypes.WINDOW_CHANGED, lambda e, p: self._on_window_changed(p))
        self.event_bus.subscribe(EventTypes.IDLE_STARTED, lambda e, p: self._on_idle_started(p))
        self.event_bus.subscribe(EventTypes.IDLE_ENDED, lambda e, p: self._on_idle_ended(p))
        self.event_bus.subscribe(EventTypes.TIMELINE_STABILITY_CHANGED, lambda e, p: self._on_stability_changed(p))
        self.event_bus.subscribe(EventTypes.BACKSPACE_BURST, lambda e, p: self._on_anomaly(p))
        self.event_bus.subscribe(EventTypes.HIGH_VELOCITY_TYPING, lambda e, p: self._on_anomaly(p))

    # --- Event Handlers ---

    def _on_window_changed(self, payload):
        self.prev_app = self.current_app
        self.prev_sector = self.current_sector
        self.current_app = payload.get("app_name", "Unknown")
        self.current_sector = payload.get("category", "General").capitalize()

        self.transition_count += 1
        self.app_visits[self.current_app] += 1
        self.sector_visits[self.current_sector] += 1

        self._add_memory(f"Subject transitioned to {self.current_app} ({self.current_sector} Sector)")

    def _on_idle_started(self, payload):
        self._add_memory("Subject entered hibernation state")

    def _on_idle_ended(self, payload):
        self.idle_count += 1
        duration = payload.get("idle_duration_seconds", 0)
        if duration > self.longest_idle:
            self.longest_idle = duration
        self._add_memory(f"Subject resumed activity after {int(duration)} seconds")

    def _on_stability_changed(self, payload):
        score = payload.get("new_value", 85)
        if score > self.highest_stability: self.highest_stability = score
        if score < self.lowest_stability: self.lowest_stability = score

    def _on_anomaly(self, payload):
        self._add_memory("Subject exhibited anomalous input behaviour")

    def _add_memory(self, summary):
        """Stores a narrative string in the rolling memory bank."""
        self.recent_events.append({
            "timestamp": time.time(),
            "summary": summary
        })

    # --- Memory Query API ---

    def get_app_visits(self, app_name):
        return self.app_visits.get(app_name, 0)

    def get_sector_visits(self, sector_name):
        return self.sector_visits.get(sector_name, 0)

    def get_most_visited_sector(self):
        if not self.sector_visits:
            return "General"
        return max(self.sector_visits, key=self.sector_visits.get)

    def get_session_duration_seconds(self):
        return time.time() - self.session_start