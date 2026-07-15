import os
import time
import random
import datetime
import threading
import sys

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import pyqtSignal, QObject

from core.event_bus import EventBus, EventTypes
from core.timeline import TimelineEngine
from core.temporal_memory import TemporalMemory
from core.prediction_engine import PredictionEngine
from narrative.template_engine import TemplateEngine
from narrative.lore_engine import LoreEngine
from monitors.window_monitor import WindowMonitor
from monitors.keyboard_monitor import KeyboardMonitor
from monitors.idle_monitor import IdleMonitor
from ui.overlay import TemporalOverlay  # <-- NEW IMPORT


# --- THREAD SAFETY BRIDGE ---
class SignalBridge(QObject):
    """Safely transports strings from the background polling thread to the main GUI thread."""
    transmission_ready = pyqtSignal(str)


# --- NARRATIVE SUBSCRIBER ---
def get_ordinal(n):
    if 11 <= (n % 100) <= 13: return str(n) + 'th'
    return str(n) + {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')


def create_transmission_subscriber(template_engine, timeline_engine, memory, lore_engine, signal_bridge):
    last_stability = 85

    def subscriber(event_type, payload):
        nonlocal last_stability

        if event_type in [EventTypes.TIMELINE_STABILITY_CHANGED, EventTypes.TIMELINE_STATE_CHANGED]:
            return

        header = "████████ TEMPORAL TRANSMISSION ████████"
        is_prediction_event = False

        if event_type == EventTypes.PREDICTION_REGISTERED:
            header = "████████ TEMPORAL FORECAST ████████"
            is_prediction_event = True
        elif event_type == EventTypes.PREDICTION_VERIFIED:
            header = "████████ PREDICTION VERIFIED ████████"
            is_prediction_event = True
        elif event_type == EventTypes.PREDICTION_AVERTED:
            header = "████████ TIMELINE DEVIATION ████████"
            is_prediction_event = True

        is_transition = (event_type == EventTypes.WINDOW_CHANGED)
        specific_template_key = event_type

        if event_type == EventTypes.WINDOW_CHANGED:
            app_visits = memory.get_app_visits(memory.current_app)
            dominant_sector = memory.get_most_visited_sector()

            if app_visits >= 3:
                if memory.current_sector == dominant_sector and memory.current_sector not in ["Coding", "System"]:
                    specific_template_key = "WindowChanged_Dominant_Deviation"
                else:
                    specific_template_key = "WindowChanged_Repeated"
            else:
                p_sec = memory.prev_sector.lower()
                c_sec = memory.current_sector.lower()
                specific_template_key = f"WindowChanged_{p_sec}_to_{c_sec}"

        elif event_type == EventTypes.IDLE_ENDED:
            if memory.idle_count >= 3:
                specific_template_key = "IdleEnded_Repeated"

        new_stability = timeline_engine.score
        delta = new_stability - last_stability

        if new_stability >= 90:
            severity = "INFO"
        elif new_stability >= 70:
            severity = "LOW"
        elif new_stability >= 50:
            severity = "MEDIUM"
        elif new_stability >= 25:
            severity = "HIGH"
        else:
            severity = "CRITICAL"

        now = datetime.datetime.now()
        future_date = now.replace(year=now.year + 21)

        rich_payload = dict(payload)
        rich_payload.update({
            "tx_id": f"TR-83B-{random.randint(10000, 99999)}",
            "future_date": future_date.strftime("%d %B %Y"),
            "transmission_age": 21,
            "subject": "Vedang",
            "old_stability": last_stability,
            "new_stability": new_stability,
            "delta": delta,
            "severity": severity,
            "is_transition": is_transition,

            "prev_app": memory.prev_app,
            "prev_sector": memory.prev_sector,
            "current_app": memory.current_app,
            "current_sector": memory.current_sector,
            "visit_count": memory.get_app_visits(memory.current_app),
            "visit_count_ordinal": get_ordinal(memory.get_app_visits(memory.current_app)),
            "dominant_sector": memory.get_most_visited_sector()
        })

        transmission = template_engine.generate_transmission(specific_template_key, rich_payload)
        if not transmission:
            transmission = template_engine.generate_transmission(event_type, rich_payload)

        if transmission:
            lines = transmission.split("\n")
            lines[0] = header
            transmission = "\n".join(lines)
            transmission = lore_engine.process(transmission, event_type, rich_payload)

            # Print to console for debugging, but ALSO emit to the UI!
            print(f"\n{transmission}\n")
            signal_bridge.transmission_ready.emit(transmission)

        if not is_prediction_event:
            last_stability = new_stability

    return subscriber


# --- BACKGROUND MONITORING LOOP ---
def run_backend(signal_bridge):
    """This function runs indefinitely in a background thread."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    templates_dir = os.path.join(current_dir, '..', 'data', 'templates')

    bus = EventBus()
    timeline_engine = TimelineEngine(bus)
    memory = TemporalMemory(bus)
    prediction_engine = PredictionEngine(bus, memory)
    template_engine = TemplateEngine(templates_dir)
    lore_engine = LoreEngine(templates_dir, injection_chance=0.08)

    narrative_subscriber = create_transmission_subscriber(
        template_engine, timeline_engine, memory, lore_engine, signal_bridge
    )

    for event_type in dir(EventTypes):
        if not event_type.startswith("__"):
            bus.subscribe(getattr(EventTypes, event_type), narrative_subscriber)

    window_monitor = WindowMonitor(bus)
    keyboard_monitor = KeyboardMonitor(bus)
    idle_monitor = IdleMonitor(bus, idle_threshold_seconds=5.0)

    keyboard_monitor.start()
    print("[Backend] Temporal Monitors Active. Awaiting events...")

    try:
        while True:
            window_monitor.poll()
            keyboard_monitor.poll()
            idle_monitor.poll()
            timeline_engine.poll()
            prediction_engine.poll()
            time.sleep(0.5)
    except Exception as e:
        print(f"Backend Thread Error: {e}")
    finally:
        keyboard_monitor.stop()


# --- MAIN GUI BOOTSTRAP ---
def main():
    print("Initializing Temporal Core Architecture...")

    # 1. Initialize the PyQt Application
    app = QApplication(sys.argv)

    # 2. Initialize the UI Overlay
    overlay = TemporalOverlay()

    # 3. Create the Thread-Safety Bridge
    bridge = SignalBridge()
    # Connect the bridge signal to the overlay's display method
    bridge.transmission_ready.connect(overlay.display_transmission)

    # 4. Start the Backend on a separate daemon thread
    backend_thread = threading.Thread(target=run_backend, args=(bridge,), daemon=True)
    backend_thread.start()

    print("\nIntegration Test Active. Desktop Overlay Engaged.")
    print("Switch windows or type fast. The transmission will appear in the top right of your screen.")
    print("Close the terminal or press Ctrl+C to terminate the program.\n")

    # 5. Start the GUI Event Loop (This blocks until the app closes)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()