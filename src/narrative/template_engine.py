import os
import json
import random


class SafeDict(dict):
    def __missing__(self, key):
        return f"[{key.upper()}_UNKNOWN]"


class TemplateEngine:
    def __init__(self, templates_dir):
        self.templates_dir = templates_dir
        self.templates = {}
        self._load_templates()

    def _load_templates(self):
        if not os.path.exists(self.templates_dir):
            return
        for filename in os.listdir(self.templates_dir):
            if filename.endswith(".json"):
                filepath = os.path.join(self.templates_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        file_data = json.load(f)
                        for event_type, template_list in file_data.items():
                            if event_type not in self.templates:
                                self.templates[event_type] = []
                            self.templates[event_type].extend(template_list)
                except Exception as e:
                    pass

    def generate_transmission(self, template_key, payload):
        """Attempts to find a template matching the key. Returns None if not found."""
        if template_key not in self.templates or not self.templates[template_key]:
            return None

        template = random.choice(self.templates[template_key])
        safe_payload = SafeDict(payload)

        behavior = template["behavior"].format_map(safe_payload)
        conclusion_label = template["conclusion_label"].format_map(safe_payload)
        conclusion_text = template["conclusion_text"].format_map(safe_payload)

        # Build the Cinematic Output
        lines = []
        lines.append("████████ TEMPORAL TRANSMISSION ████████")
        lines.append("")
        lines.append(f"Archive ID:        {payload.get('tx_id')}")
        lines.append(f"Recovered:         {payload.get('future_date')}")
        lines.append(f"Transmission Age:  {payload.get('transmission_age')} Years")
        lines.append(f"Subject:           {payload.get('subject')}")
        lines.append("")

        if payload.get('is_transition'):
            lines.append(f"Previous Sector:       {payload.get('prev_sector')}")
            lines.append(f"Previous Application:  {payload.get('prev_app')}")
            lines.append(f"Current Sector:        {payload.get('current_sector')}")
            lines.append(f"Current Application:   {payload.get('current_app')}")
        else:
            lines.append(f"Active Sector:         {payload.get('current_sector')}")
            lines.append(f"Active Application:    {payload.get('current_app')}")

        lines.append("")
        lines.append("Observed Behaviour:")
        lines.append(behavior)
        lines.append("")

        old_stab = payload.get('old_stability')
        new_stab = payload.get('new_stability')
        delta = payload.get('delta')

        # Format the visual arrow
        if new_stab > old_stab:
            arrow = "↑"
        elif new_stab < old_stab:
            arrow = "↓"
        else:
            arrow = "≡"

        delta_str = f"+{delta}" if delta > 0 else str(delta)

        lines.append(f"Timeline Stability:    {old_stab}% {arrow} {new_stab}%")
        lines.append(f"Confidence Delta:      {delta_str}%")
        lines.append(f"Severity:              {payload.get('severity')}")
        lines.append("")

        lines.append(f"{conclusion_label}:")
        lines.append(conclusion_text)
        lines.append("██████████████████████████████████████")

        return "\n".join(lines)