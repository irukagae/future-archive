import os
import time
import random
import datetime
from core.event_bus import EventBus, EventTypes
from core.timeline import TimelineEngine
from monitors.window_monitor import WindowMonitor
from monitors.keyboard_monitor import KeyboardMonitor
from monitors.idle_monitor import IdleMonitor
from narrative.template_engine import TemplateEngine


class TransmissionContext:
    def __init__(self):
        self.current_app = "System"
        self.current_sector = "General"
        self.prev_app = "System"
        self.prev_sector = "General"
        self.last_stability = 85


def create_transmission_subscriber(template_engine, timeline_engine):
    context = TransmissionContext()

    def subscriber(event_type, payload):
        primary_events = [
            EventTypes.WINDOW_CHANGED,
            EventTypes.HIGH_VELOCITY_TYPING,
            EventTypes.BACKSPACE_BURST,
            EventTypes.IDLE_STARTED,
            EventTypes.IDLE_ENDED
        ]
        if event_type not in primary_events:
            return

        is_transition = False
        specific_template_key = event_type

        # 1. Update Context & Determine Template Key
        if event_type == EventTypes.WINDOW_CHANGED:
            is_transition = True
            context.prev_app = context.current_app
            context.prev_sector = context.current_sector
            context.current_app = payload.get("app_name", "General")
            context.current_sector = payload.get("category", "General").capitalize()

            # Generate contextual template key (e.g., "WindowChanged_coding_to_browser")
            p_sec = context.prev_sector.lower()
            c_sec = context.current_sector.lower()
            specific_template_key = f"WindowChanged_{p_sec}_to_{c_sec}"

        # 2. Extract Stability Metrics
        new_stability = timeline_engine.score
        delta = new_stability - context.last_stability

        # 3. Believable Severity Scale
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

        # 4. Future Temporal Presentation
        now = datetime.datetime.now()
        transmission_age = 21
        future_date = now.replace(year=now.year + transmission_age)

        # 5. Build Payload
        rich_payload = dict(payload)
        rich_payload.update({
            "tx_id": f"TR-83B-{random.randint(10000, 99999)}",
            "future_date": future_date.strftime("%d %B %Y"),
            "transmission_age": transmission_age,
            "subject": "Vedang",
            "prev_app": context.prev_app,
            "prev_sector": context.prev_sector,
            "current_app": context.current_app,
            "current_sector": context.current_sector,
            "old_stability": context.last_stability,
            "new_stability": new_stability,
            "delta": delta,
            "severity": severity,
            "is_transition": is_transition
        })

        # 6. Generate Transmission (Try specific context first, fallback to generic event type)
        transmission = template_engine.generate_transmission(specific_template_key, rich_payload)
        if not transmission:
            transmission = template_engine.generate_transmission(event_type, rich_payload)

        if transmission:
            print(f"\n{transmission}\n")

        # 7. Finalize State
        context.last_stability = new_stability

    return subscriber


def main():
    print("Initializing Temporal Core Architecture...")

    current_dir = os.path.dirname(os.path.abspath(__file__))
    templates_dir = os.path.join(current_dir, '..', 'data', 'templates')

    bus = EventBus()
    timeline_engine = TimelineEngine(bus)
    template_engine = TemplateEngine(templates_dir)

    narrative_subscriber = create_transmission_subscriber(template_engine, timeline_engine)

    for event_type in dir(EventTypes):
        if not event_type.startswith("__"):
            bus.subscribe(getattr(EventTypes, event_type), narrative_subscriber)

    window_monitor = WindowMonitor(bus)
    keyboard_monitor = KeyboardMonitor(bus)
    idle_monitor = IdleMonitor(bus, idle_threshold_seconds=5.0)

    keyboard_monitor.start()

    print("\nIntegration Test Active. Cinematic Output Engaged.")
    print("Intercepting Transmissions from Timeline 83-B...")
    print("Press Ctrl+C to terminate.\n")

    try:
        while True:
            window_monitor.poll()
            keyboard_monitor.poll()
            idle_monitor.poll()
            timeline_engine.poll()
            time.sleep(0.5)

    except KeyboardInterrupt:
        pass
    finally:
        keyboard_monitor.stop()


if __name__ == "__main__":
    main()