import time
from core.event_bus import EventBus, EventTypes
from core.timeline import TimelineEngine
from monitors.window_monitor import WindowMonitor
from monitors.keyboard_monitor import KeyboardMonitor
from monitors.idle_monitor import IdleMonitor


def generic_subscriber(event_type, payload):
    """Silently logs generic events so they don't clutter the console."""
    # We leave this blank for now so we can focus solely on Timeline events.
    # The Event Bus is still routing them under the hood.
    pass


def timeline_subscriber(event_type, payload):
    """A formatted subscriber dedicated to testing Timeline Engine outputs."""
    print("")  # Spacer

    if event_type == EventTypes.TIMELINE_STABILITY_CHANGED:
        prev = payload.get('previous_value')
        new = payload.get('new_value')
        reason = payload.get('reason')

        # Format a nice arrow showing direction
        arrow = "↑" if new > prev else "↓"
        print(f"[TIMELINE ENGINE] Stability: {prev} -> {new} {arrow}")
        print(f"                  Reason: {reason}")

    elif event_type == EventTypes.TIMELINE_STATE_CHANGED:
        old_state = payload.get('old_state')
        new_state = payload.get('new_state')
        current = payload.get('current_stability')
        print(f"!!! [TIMELINE ENGINE] STATE CHANGE: {old_state} -> {new_state} (Score: {current}) !!!")


def main():
    print("Initializing Temporal Core Architecture...")

    # 1. Create the Event Bus
    bus = EventBus()

    # 2. Register Generic Subscriber (to prove the monitors are still firing)
    bus.subscribe(EventTypes.WINDOW_CHANGED, generic_subscriber)
    bus.subscribe(EventTypes.HIGH_VELOCITY_TYPING, generic_subscriber)
    bus.subscribe(EventTypes.BACKSPACE_BURST, generic_subscriber)
    bus.subscribe(EventTypes.IDLE_STARTED, generic_subscriber)
    bus.subscribe(EventTypes.IDLE_ENDED, generic_subscriber)

    # 3. Register Timeline Subscriber
    bus.subscribe(EventTypes.TIMELINE_STABILITY_CHANGED, timeline_subscriber)
    bus.subscribe(EventTypes.TIMELINE_STATE_CHANGED, timeline_subscriber)

    # 4. Initialize Core Systems
    timeline_engine = TimelineEngine(bus)

    # 5. Initialize Monitors
    window_monitor = WindowMonitor(bus)
    keyboard_monitor = KeyboardMonitor(bus)
    idle_monitor = IdleMonitor(bus, idle_threshold_seconds=5.0)

    # 6. Start background listeners
    keyboard_monitor.start()

    print("\nIntegration Test Active. Timeline Engine is monitoring events.")
    print("Baseline: 85. Try reducing stability to below 80 to see a State Change.")
    print("Press Ctrl+C to terminate the session.\n")

    # 7. Main Polling Loop
    try:
        while True:
            window_monitor.poll()
            keyboard_monitor.poll()
            idle_monitor.poll()
            timeline_engine.poll()  # Process natural drift

            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\nTermination signal received.")
    finally:
        keyboard_monitor.stop()
        print("Temporal Monitors powered down.")


if __name__ == "__main__":
    main()