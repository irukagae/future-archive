from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QFrame
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCore import Qt


class Theme:
    """Centralized color and typography definitions."""
    BG_COLOR = "rgba(18, 18, 20, 245)"
    BORDER = "#2A2A2E"
    TEXT_PRIMARY = "#E2E2E2"
    TEXT_SECONDARY = "#8A8A93"
    TEXT_MUTED = "#5C5C66"

    SEVERITY_COLORS = {
        "INFO": "#8A8A93",  # Neutral Gray
        "LOW": "#00E5FF",  # Cool Cyan
        "MEDIUM": "#FFB300",  # Amber
        "HIGH": "#FF9100",  # Orange
        "CRITICAL": "#FF1744"  # Red
    }

    @staticmethod
    def get_font(size, bold=False):
        # Uses standard coding fonts with fallbacks
        font = QFont("Cascadia Code", size)
        font.setStyleHint(QFont.StyleHint.Monospace)
        font.setBold(bold)
        return font


class Divider(QFrame):
    def __init__(self, style="solid"):
        super().__init__()
        self.setFrameShape(QFrame.Shape.HLine)
        if style == "dashed":
            self.setStyleSheet(f"border-top: 1px dashed {Theme.TEXT_MUTED};")
        else:
            self.setStyleSheet(f"background-color: {Theme.BORDER};")
        self.setFixedHeight(1)


class SectionTitle(QLabel):
    def __init__(self, text):
        super().__init__(text.upper())
        self.setFont(Theme.get_font(8, bold=True))
        self.setStyleSheet(f"color: {Theme.TEXT_MUTED}; letter-spacing: 1px;")


class BodyText(QLabel):
    def __init__(self, text, color=Theme.TEXT_PRIMARY):
        super().__init__(text)
        self.setFont(Theme.get_font(10))
        self.setStyleSheet(f"color: {color}; line-height: 1.4;")
        self.setWordWrap(True)


class StabilityWidget(QWidget):
    """The most visually prominent component in the overlay."""

    def __init__(self, old_val, new_val, delta, severity):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        color = Theme.SEVERITY_COLORS.get(severity, Theme.SEVERITY_COLORS["INFO"])

        # Determine visual arrow
        arrow = "→"
        if delta.startswith('+') and delta != "+0":
            arrow = "↑"
        elif delta.startswith('-'):
            arrow = "↓"

        val_label = QLabel(f"{old_val} {arrow} {new_val}")
        val_label.setFont(Theme.get_font(20, bold=True))
        val_label.setStyleSheet(f"color: {color};")

        delta_label = QLabel(f"({delta}%)")
        delta_label.setFont(Theme.get_font(12, bold=True))
        delta_label.setStyleSheet(f"color: {color};")

        layout.addWidget(val_label)
        layout.addWidget(delta_label)
        layout.addStretch()


class TransmissionCard(QFrame):
    """The main modular information card that replaces the raw text block."""

    def __init__(self, parsed_data):
        super().__init__()
        self.setObjectName("MainCard")
        self.setStyleSheet(f"""
            QFrame#MainCard {{
                background-color: {Theme.BG_COLOR};
                border: 1px solid {Theme.BORDER};
                border-radius: 8px;
            }}
        """)
        # Compact horizontal size
        self.setFixedWidth(420)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # 1. Header
        header = QLabel(parsed_data["header"])
        header_color = Theme.SEVERITY_COLORS.get(parsed_data["severity"], Theme.TEXT_PRIMARY)
        header.setFont(Theme.get_font(11, bold=True))
        header.setStyleSheet(f"color: {header_color}; letter-spacing: 2px;")
        layout.addWidget(header)
        layout.addWidget(Divider())

        # 2. Behavior
        beh_layout = QVBoxLayout()
        beh_layout.setSpacing(4)
        beh_layout.addWidget(SectionTitle("Current Behaviour"))
        beh_layout.addWidget(BodyText(parsed_data["behavior"]))
        layout.addLayout(beh_layout)

        # 3. Timeline Stability (Visual focal point)
        stab_layout = QVBoxLayout()
        stab_layout.setSpacing(2)
        stab_layout.addWidget(SectionTitle("Timeline Stability"))
        stab_layout.addWidget(StabilityWidget(
            parsed_data["stability_old"],
            parsed_data["stability_new"],
            parsed_data["delta"],
            parsed_data["severity"]
        ))
        layout.addLayout(stab_layout)

        # 4. Temporal Analysis
        if parsed_data["analysis_text"]:
            ana_layout = QVBoxLayout()
            ana_layout.setSpacing(4)
            ana_layout.addWidget(SectionTitle(parsed_data["analysis_title"]))
            ana_layout.addWidget(BodyText(parsed_data["analysis_text"], color=Theme.TEXT_SECONDARY))
            layout.addLayout(ana_layout)

        layout.addWidget(Divider())

        # 5. Metadata (Small, dense text)
        meta_layout = QVBoxLayout()
        meta_layout.setSpacing(2)
        meta_text = "\n".join(parsed_data["metadata"])
        meta_label = BodyText(meta_text, color=Theme.TEXT_MUTED)
        meta_label.setFont(Theme.get_font(9))
        meta_layout.addWidget(meta_label)
        layout.addLayout(meta_layout)

        # 6. Lore Fragment (Only added if present)
        if parsed_data["lore"]:
            layout.addSpacing(8)
            layout.addWidget(Divider(style="dashed"))
            lore_layout = QVBoxLayout()
            lore_layout.setSpacing(4)
            lore_layout.addWidget(SectionTitle("RESTRICTED METADATA"))
            lore_label = BodyText(parsed_data["lore"], color="#A79CE5")  # Subtle purple tint
            lore_label.setFont(Theme.get_font(9, bold=True))
            lore_layout.addWidget(lore_label)
            layout.addLayout(lore_layout)