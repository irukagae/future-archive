import os
import time
import random
import datetime
from core.event_bus import EventBus, EventTypes
from core.timeline import TimelineEngine
from core.temporal_memory import TemporalMemory
from monitors.window_monitor import WindowMonitor
from monitors.keyboard_monitor import KeyboardMonitor
from monitors.idle_monitor import IdleMonitor
from narrative.template_engine import TemplateEngine


def get_ordinal(n):
    """Helper to convert 3 to '3rd', 4 to '4th', etc."""
    if 11 <= (n % 100) <= 13:
        return str(n) + 'th'
    return str(n) + {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')


def create_transmission_subscriber(template_engine, timeline_engine, memory):
    last_stability = 85  # Local baseline tracker

    def subscriber(event_type, payload):
        nonlocal last_stability

        primary_events = [
            EventTypes.WINDOW_CHANGED,
            EventTypes.HIGH_VELOCITY_TYPING,
            EventTypes.BACKSPACE_BURST,
            EventTypes.IDLE_STARTED,
            EventTypes.IDLE_ENDED
        ]
        if event_type not in primary_events:
            return

        is_transition = (event_type == EventTypes.WINDOW_CHANGED)
        specific_template_key = event_type

        # 1. Memory Integration Logic
        if event_type == EventTypes.WINDOW_CHANGED:
            app_visits = memory.get_app_visits(memory.current_app)
            dominant_sector = memory.get_most_visited_sector()

            # Determine if this is a repetitive behavioral loop
            if app_visits >= 3:
                # If they are mostly hanging out in a non-coding sector, call it out
                if memory.current_sector == dominant_sector and memory.current_sector not in ["Coding", "System"]:
                    specific_template_key = "WindowChanged_Dominant_Deviation"
                else:
                    specific_template_key = "WindowChanged_Repeated"
            else:
                # Fallback to standard contextual keys (e.g., Coding to Browser)
                p_sec = memory.prev_sector.lower()
                c_sec = memory.current_sector.lower()
                specific_template_key = f"WindowChanged_{p_sec}_to_{c_sec}"

        elif event_type == EventTypes.IDLE_ENDED:
            if memory.idle_count >= 3:
                specific_template_key = "IdleEnded_Repeated"

        # 2. Extract Stability Metrics
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

        # 3. Future Temporal Presentation
        now = datetime.datetime.now()
        future_date = now.replace(year=now.year + 21)

        # 4. Build Memory-Enriched Payload
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

            # Memory Injections
            "prev_app": memory.prev_app,
            "prev_sector": memory.prev_sector,
            "current_app": memory.current_app,
            "current_sector": memory.current_sector,
            "visit_count": memory.get_app_visits(memory.current_app),
            "visit_count_ordinal": get_ordinal(memory.get_app_visits(memory.current_app)),
            "dominant_sector": memory.get_most_visited_sector(),
            "idle_count_ordinal": get_ordinal(memory.idle_count)
        })

        # 5. Generate Transmission
        transmission = template_engine.generate_transmission(specific_template_key, rich_payload)
        if not transmission:
            transmission = template_engine.generate_transmission(event_type, rich_payload)

        if transmission:
            print(f"\n{transmission}\n")

        # 6. Finalize State
        last_stability = new_stability

    return subscriber


def main():
    print("Initializing Temporal Core Architecture...")

    current_dir = os.path.dirname(os.path.abspath(__file__))
    templates_dir = os.path.join(current_dir, '..', 'data', 'templates')

    bus = EventBus()

    # ORDER OF REGISTRATION MATTERS:
    # 1. Timeline calculates the score
    # 2. Memory tracks the facts
    # 3. Subscriber generates the story using the updated facts
    timeline_engine = TimelineEngine(bus)
    memory = TemporalMemory(bus)
    template_engine = TemplateEngine(templates_dir)

    narrative_subscriber = create_transmission_subscriber(template_engine, timeline_engine, memory)

    for event_type in dir(EventTypes):
        if not event_type.startswith("__"):
            bus.subscribe(getattr(EventTypes, event_type), narrative_subscriber)

    window_monitor = WindowMonitor(bus)
    keyboard_monitor = KeyboardMonitor(bus)
    idle_monitor = IdleMonitor(bus, idle_threshold_seconds=5.0)

    keyboard_monitor.start()

    print("\nIntegration Test Active. Temporal Memory Engaged.")
    print("Test Memory by entering the same application multiple times.")
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