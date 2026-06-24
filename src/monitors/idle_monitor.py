import time
import ctypes
from ctypes import wintypes

import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from src.core.event_bus import EventTypes, EventBus


class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.UINT),
                ("dwTime", wintypes.DWORD)]


class IdleMonitor:
    def __init__(self, event_bus, idle_threshold_seconds=60.0):
        self.event_bus = event_bus
        self.idle_threshold = idle_threshold_seconds
        self.is_idle = False
        self.idle_start_time = 0.0

        self.last_input_info = LASTINPUTINFO()
        self.last_input_info.cbSize = ctypes.sizeof(LASTINPUTINFO)

    def _get_idle_time_seconds(self):
        if ctypes.windll.user32.GetLastInputInfo(ctypes.byref(self.last_input_info)):
            tick_count = ctypes.windll.kernel32.GetTickCount()
            idle_time_ms = tick_count - self.last_input_info.dwTime
            return idle_time_ms / 1000.0
        return 0.0

    def _format_duration(self, total_seconds):
        mins, secs = divmod(int(total_seconds), 60)
        hours, mins = divmod(mins, 60)
        parts = []
        if hours > 0: parts.append(f"{hours} hours")
        if mins > 0: parts.append(f"{mins} minutes")
        if secs > 0 or not parts: parts.append(f"{secs} seconds")
        return " ".join(parts)

    def poll(self):
        current_idle_seconds = self._get_idle_time_seconds()
        now = time.time()

        # PUBLISH IDLE STARTED
        if current_idle_seconds >= self.idle_threshold and not self.is_idle:
            self.is_idle = True
            self.idle_start_time = now - current_idle_seconds

            self.event_bus.publish(EventTypes.IDLE_STARTED, {
                "idle_threshold": self.idle_threshold
            })

        # PUBLISH IDLE ENDED
        elif current_idle_seconds < self.idle_threshold and self.is_idle:
            self.is_idle = False
            duration = now - self.idle_start_time
            formatted_duration = self._format_duration(duration)

            self.event_bus.publish(EventTypes.IDLE_ENDED, {
                "idle_duration_seconds": duration,
                "formatted_duration": formatted_duration
            })


if __name__ == "__main__":
    test_bus = EventBus()
    test_bus.subscribe(EventTypes.IDLE_STARTED, lambda e, p: print(f"[{e}] {p}"))
    test_bus.subscribe(EventTypes.IDLE_ENDED, lambda e, p: print(f"[{e}] {p}"))

    monitor = IdleMonitor(test_bus, idle_threshold_seconds=5.0)
    print("Idle Monitor running in standalone mode (PubSub). Press Ctrl+C to stop.")
    try:
        while True:
            monitor.poll()
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass