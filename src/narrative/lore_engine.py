import os
import json
import random
from src.core.event_bus import EventTypes


class LoreEngine:
    def __init__(self, templates_dir, injection_chance=0.08):
        """
        :param injection_chance: 0.08 = 8% chance to append a lore fragment.
        """
        self.templates_dir = templates_dir
        self.injection_chance = injection_chance
        self.fragments = {}
        self._load_fragments()

    def _load_fragments(self):
        filepath = os.path.join(self.templates_dir, 'lore.json')
        if not os.path.exists(filepath):
            return

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                self.fragments = json.load(f)
        except Exception as e:
            print(f"[Lore Engine Error] Failed to load lore.json: {e}")

    def _determine_category(self, event_type, payload):
        """Selects the most appropriate lore category based on the current context."""
        if event_type == EventTypes.PREDICTION_VERIFIED:
            return "prediction_verified"
        if event_type == EventTypes.PREDICTION_AVERTED:
            return "prediction_averted"
        if event_type in [EventTypes.BACKSPACE_BURST, EventTypes.HIGH_VELOCITY_TYPING]:
            return "anomaly"

        # Check for repeated behavioral loops provided by Temporal Memory
        visit_count = payload.get("visit_count", 0)
        idle_count = payload.get("idle_count_ordinal", "1st")
        if visit_count >= 3 or not idle_count.startswith("1"):
            return "repeated_loop"

        return "generic"

    def process(self, transmission_text, event_type, payload):
        """
        Rolls for a lore injection. If successful, splices the lore block
        into the transmission just above the final footer.
        """
        if not transmission_text or not self.fragments:
            return transmission_text

        # The Golden Rule: Rarity
        if random.random() > self.injection_chance:
            return transmission_text

        category = self._determine_category(event_type, payload)

        # Fallback to generic if the category doesn't exist
        if category not in self.fragments or not self.fragments[category]:
            category = "generic"

        fragment = random.choice(self.fragments[category])

        # Format the lore block
        lore_block = (
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "[RESTRICTED METADATA]\n"
            f"{fragment}\n"
        )

        # Splice it into the transmission right before the final closing border
        footer = "██████████████████████████████████████"
        if footer in transmission_text:
            return transmission_text.replace(footer, lore_block + footer)

        # Fallback if border is missing for some reason
        return transmission_text + "\n" + lore_block