import collections
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt, QPropertyAnimation, QTimer
from PyQt6.QtGui import QFont, QColor


class TemporalOverlay(QWidget):
    def __init__(self):
        super().__init__()

        # 1. Window Flags: Frameless, Always on Top, Click-Through, No Taskbar Icon
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.WindowTransparentForInput |
            Qt.WindowType.Tool
        )

        # 2. Transparent Background
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # 3. Setup Layout and Text Label (Minimal, readable styling)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.text_label = QLabel("")
        self.text_label.setFont(QFont("Consolas", 11))
        self.text_label.setStyleSheet("""
            QLabel {
                color: #E0E0E0;
                background-color: rgba(15, 15, 15, 210);
                padding: 20px;
                border-left: 3px solid #555555;
                border-radius: 4px;
            }
        """)
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        self.layout.addWidget(self.text_label)

        # 4. Queue and Animation State
        self.message_queue = collections.deque()
        self.is_displaying = False

        # Initial opacity is 0 (invisible)
        self.setWindowOpacity(0.0)

        # 5. Animation Setup
        self.fade_anim = QPropertyAnimation(self, b"windowOpacity")
        self.fade_anim.setDuration(800)  # 800ms fade time

        # Hold timer: how long the message stays fully visible
        self.hold_timer = QTimer(self)
        self.hold_timer.setSingleShot(True)
        self.hold_timer.timeout.connect(self._start_fade_out)

        self.fade_anim.finished.connect(self._on_animation_finished)

    def display_transmission(self, transmission_text):
        """Public API: Add a transmission to the queue."""
        self.message_queue.append(transmission_text)
        self._process_queue()

    def _process_queue(self):
        """Processes the next message if the overlay is currently idle."""
        if self.is_displaying or not self.message_queue:
            return

        self.is_displaying = True
        next_message = self.message_queue.popleft()

        self.text_label.setText(next_message)
        self.adjustSize()
        self._reposition()

        # Show and start fade-in
        self.show()
        self._start_fade_in()

    def _reposition(self):
        """Places the overlay in the top-right corner with a small margin."""
        screen = self.screen().availableGeometry()
        margin_x = 40
        margin_y = 40

        # Calculate X and Y coordinates
        x = screen.width() - self.width() - margin_x
        y = margin_y

        self.move(x, y)

    def _start_fade_in(self):
        self.fade_anim.setStartValue(0.0)
        self.fade_anim.setEndValue(1.0)
        self.fade_anim.start()

    def _start_fade_out(self):
        self.fade_anim.setStartValue(1.0)
        self.fade_anim.setEndValue(0.0)
        self.fade_anim.start()

    def _on_animation_finished(self):
        if self.windowOpacity() == 1.0:
            # Fade-in finished, hold for 6 seconds
            self.hold_timer.start(6000)
        elif self.windowOpacity() == 0.0:
            # Fade-out finished, hide window and check queue
            self.hide()
            self.is_displaying = False
            self._process_queue()