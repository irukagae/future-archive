import time
from enum import IntEnum
from PyQt6.QtCore import QObject, pyqtSlot
from .parser import TransmissionParser


class Priority(IntEnum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


class NotificationManager(QObject):
    def __init__(self, overlay):
        super().__init__()
        self.overlay = overlay
        self.overlay.overlay_freed.connect(self._on_overlay_freed)

        # State Management
        self.current_priority = None
        self.queue = []  # Stores tuples of (Priority, parsed_data, duration_ms)

        # Coalescing / Burst tracking
        self.burst_buffer = []  # Stores (timestamp, sector, parsed_data)
        self.burst_window_seconds = 4.0

    def _get_priority_and_duration(self, data):
        """Determines priority and display lifetime based on content."""
        header = data.get("header", "")
        severity = data.get("severity", "INFO")
        behavior = data.get("behavior", "").lower()

        if "VERIFIED" in header or "DEVIATION" in header or severity == "CRITICAL":
            return Priority.CRITICAL, 8000
        elif "FORECAST" in header or severity == "HIGH":
            return Priority.HIGH, 5000
        elif "hibernation" in behavior or "resumed activity" in behavior:
            return Priority.HIGH, 4000
        elif severity in ["MEDIUM", "LOW", "INFO"]:
            return Priority.NORMAL, 2500
        return Priority.LOW, 2000

    @pyqtSlot(str)
    def process_transmission(self, raw_text):
        """Entry point from the Backend Signal Bridge."""
        parsed_data = TransmissionParser.parse(raw_text)
        priority, duration = self._get_priority_and_duration(parsed_data)
        now = time.time()

        # 1. Burst Coalescing (Only applies to NORMAL priority, e.g., rapid window switching)
        if priority == Priority.NORMAL:
            self.burst_buffer.append((now, parsed_data.get("current_sector", "Unknown"), parsed_data))
            # Prune old buffer items
            self.burst_buffer = [i for i in self.burst_buffer if now - i[0] <= self.burst_window_seconds]

            # If 3 or more routine events happen quickly, merge them
            if len(self.burst_buffer) >= 3:
                parsed_data = self._create_coalesced_card(self.burst_buffer)
                self.burst_buffer.clear()
                # Coalesced cards get a slightly longer duration
                duration = 3500
        else:
            # High/Critical events reset the routine burst buffer
            self.burst_buffer.clear()

        # 2. Priority Logic State Machine
        if priority >= Priority.HIGH:
            # High/Critical always get queued to ensure they are seen
            self.queue.append((priority, parsed_data, duration))
            self.queue.sort(key=lambda x: x[0], reverse=True)  # Sort by highest priority

            if self.current_priority is None:
                self._pop_and_play()
            elif self.current_priority < priority:
                # Force current lower-priority card to fade out immediately to make room
                self.overlay.force_finish()

        elif priority == Priority.NORMAL:
            if self.current_priority in [Priority.CRITICAL, Priority.HIGH]:
                # Routine data is obsolete if we are currently looking at something important. Discard.
                pass
            elif self.current_priority == Priority.NORMAL:
                # Interrupt and replace the current routine notification (Crossfade)
                self.overlay.interrupt_card(parsed_data, duration)
            else:
                # Screen is idle
                self.current_priority = priority
                self.overlay.display_card(parsed_data, duration)

    def _create_coalesced_card(self, buffer):
        """Merges multiple routine events into a single intelligent summary card."""
        sectors = [item[1] for item in buffer if item[1] != "Unknown"]
        first_data = buffer[0][2]
        last_data = buffer[-1][2]

        # Safely strip the '%' sign so Python can do the math without crashing
        def safe_int(val, default=85):
            try:
                return int(str(val).replace('%', '').strip())
            except ValueError:
                return default

        old_stab = safe_int(first_data.get("stability_old", 85))
        new_stab = safe_int(last_data.get("stability_new", 85))
        delta = new_stab - old_stab

        return {
            "header": "TEMPORAL TRANSMISSION",
            "metadata": [f"Recent Activity Sequence:", f"{' → '.join(sectors)}"],
            "behavior": "Rapid workflow transitions detected across multiple sectors.",
            "stability_old": f"{old_stab}%",
            "stability_new": f"{new_stab}%",
            "delta": f"+{delta}%" if delta > 0 else f"{delta}%",
            "severity": "MEDIUM",
            "analysis_title": "OBSERVATION",
            "analysis_text": "High-frequency context switching. System discarding obsolete intermediate states to maintain temporal focus.",
            "lore": None,
            "current_sector": "Burst"
        }

    @pyqtSlot()
    def _on_overlay_freed(self):
        """Called when the overlay has completely faded out and is empty."""
        self.current_priority = None
        if self.queue:
            self._pop_and_play()

    def _pop_and_play(self):
        priority, data, duration = self.queue.pop(0)
        self.current_priority = priority
        self.overlay.display_card(data, duration)