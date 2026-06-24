import time
from pynput import keyboard

import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from src.core.event_bus import EventTypes, EventBus


class KeyboardMonitor:
    def __init__(self, event_bus):
        self.event_bus = event_bus
        self.total_keys = 0
        self.backspace_count = 0
        self.enter_count = 0

        self.key_timestamps = []
        self.backspace_timestamps = []

        self.kpm_window_seconds = 10.0
        self.high_velocity_kpm = 250
        self.backspace_burst_window = 5.0
        self.backspace_burst_threshold = 6

        self.last_velocity_alert_time = 0
        self.last_backspace_alert_time = 0

        self.listener = None

    def on_press(self, key):
        now = time.time()
        self.key_timestamps.append(now)
        self.total_keys += 1

        if key == keyboard.Key.backspace:
            self.backspace_timestamps.append(now)
            self.backspace_count += 1
        elif key == keyboard.Key.enter:
            self.enter_count += 1

    def _clean_old_timestamps(self, timestamps, window_size, current_time):
        cutoff_time = current_time - window_size
        while timestamps and timestamps[0] < cutoff_time:
            timestamps.pop(0)

    def start(self):
        self.listener = keyboard.Listener(on_press=self.on_press)
        self.listener.start()

    def stop(self):
        if self.listener:
            self.listener.stop()

    def poll(self):
        now = time.time()
        self._clean_old_timestamps(self.key_timestamps, self.kpm_window_seconds, now)
        self._clean_old_timestamps(self.backspace_timestamps, self.backspace_burst_window, now)

        multiplier = 60.0 / self.kpm_window_seconds
        current_kpm = int(len(self.key_timestamps) * multiplier)

        # PUBLISH HIGH VELOCITY TYPING
        if current_kpm >= self.high_velocity_kpm:
            if (now - self.last_velocity_alert_time) > 10.0:
                self.event_bus.publish(EventTypes.HIGH_VELOCITY_TYPING, {
                    "current_kpm": current_kpm
                })
                self.last_velocity_alert_time = now

        # PUBLISH BACKSPACE BURST
        if len(self.backspace_timestamps) >= self.backspace_burst_threshold:
            if (now - self.last_backspace_alert_time) > 5.0:
                self.event_bus.publish(EventTypes.BACKSPACE_BURST, {
                    "backspace_count": len(self.backspace_timestamps)
                })
                self.last_backspace_alert_time = now


if __name__ == "__main__":
    test_bus = EventBus()
    test_bus.subscribe(EventTypes.HIGH_VELOCITY_TYPING, lambda e, p: print(f"[{e}] {p}"))
    test_bus.subscribe(EventTypes.BACKSPACE_BURST, lambda e, p: print(f"[{e}] {p}"))

    monitor = KeyboardMonitor(test_bus)
    monitor.start()
    print("Keyboard Monitor running in standalone mode (PubSub). Press Ctrl+C to stop.")
    try:
        while True:
            monitor.poll()
            time.sleep(1)
    except KeyboardInterrupt:
        monitor.stop()