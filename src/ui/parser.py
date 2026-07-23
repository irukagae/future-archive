import re


class TransmissionParser:
    @staticmethod
    def parse(raw_text):
        data = {
            "header": "TEMPORAL TRANSMISSION",
            "metadata": [],
            "behavior": "",
            "stability_old": "",
            "stability_new": "",
            "delta": "",
            "severity": "INFO",
            "analysis_title": "TEMPORAL ANALYSIS",
            "analysis_text": "",
            "lore": None,
            "current_sector": "Unknown"  # <-- NEW: Used for coalescing
        }

        lines = [line.strip() for line in raw_text.split('\n') if line.strip()]
        if not lines:
            return data

        # 1. Header
        data["header"] = lines[0].replace('█', '').strip()

        # 2. Metadata & Sector
        for line in lines[1:]:
            if "Observed Behaviour:" in line or "Observed Behavior:" in line:
                break
            if ':' in line and not line.startswith('█'):
                data["metadata"].append(line)
                # Extract the sector explicitly for the Notification Manager
                if "Current Sector:" in line or "Active Sector:" in line:
                    data["current_sector"] = line.split(":", 1)[1].strip()

        # 3. Behavior
        beh_match = re.search(r'Observed Behaviour:\s*(.*?)(?=\n\s*\n|\nTimeline)', raw_text, re.DOTALL)
        if beh_match:
            data["behavior"] = beh_match.group(1).strip()

        # 4. Stability & Severity
        stab_match = re.search(r'Timeline Stability:\s+(.*)', raw_text)
        if stab_match:
            parts = stab_match.group(1).split()
            if len(parts) >= 3:
                data["stability_old"] = parts[0]
                data["stability_new"] = parts[2]
            else:
                data["stability_old"] = parts[0]
                data["stability_new"] = parts[0]

        delta_match = re.search(r'Confidence Delta:\s+(.*)', raw_text)
        if delta_match:
            data["delta"] = delta_match.group(1)

        sev_match = re.search(r'Severity:\s+(\w+)', raw_text)
        if sev_match:
            data["severity"] = sev_match.group(1).upper()

        # 5. Analysis
        analysis_match = re.search(r'Severity:\s+\w+\s+(.*?)(?=\n[━█]|\n\[RESTRICTED|$)', raw_text, re.DOTALL)
        if analysis_match:
            analysis_chunk = analysis_match.group(1).strip()
            chunk_lines = analysis_chunk.split('\n', 1)
            data["analysis_title"] = chunk_lines[0].replace(':', '').strip()
            if len(chunk_lines) > 1:
                data["analysis_text"] = chunk_lines[1].strip().replace('\n', ' ')

        # 6. Lore
        lore_match = re.search(r'\[RESTRICTED METADATA\]\s*(.*?)(?=\n█|$)', raw_text, re.DOTALL)
        if lore_match:
            data["lore"] = lore_match.group(1).strip()

        return data