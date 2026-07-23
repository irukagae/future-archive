from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import Qt, QPropertyAnimation, QParallelAnimationGroup, QTimer, QPoint, QEasingCurve, pyqtSignal
from .components import TransmissionCard


class TemporalOverlay(QWidget):
    # Signal emitted when the overlay is fully hidden and ready for a new command
    overlay_freed = pyqtSignal()

    def __init__(self):
        super().__init__()

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.WindowTransparentForInput |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.current_card = None
        self.next_card_data = None

        self.setWindowOpacity(0.0)

        # Animations
        self.anim_group = QParallelAnimationGroup(self)
        self.fade_anim = QPropertyAnimation(self, b"windowOpacity")
        self.slide_anim = QPropertyAnimation(self, b"pos")

        self.fade_anim.setDuration(400)  # Faster fades for snappier UI
        self.slide_anim.setDuration(600)
        self.slide_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.anim_group.addAnimation(self.fade_anim)
        self.anim_group.addAnimation(self.slide_anim)
        self.anim_group.finished.connect(self._on_animation_finished)

        # Hold Timer
        self.hold_timer = QTimer(self)
        self.hold_timer.setSingleShot(True)
        self.hold_timer.timeout.connect(self._start_fade_out)

    def display_card(self, parsed_data, duration_ms):
        """Displays a card cleanly from an idle state."""
        self.current_duration = duration_ms

        if self.current_card:
            self.layout.removeWidget(self.current_card)
            self.current_card.deleteLater()

        self.current_card = TransmissionCard(parsed_data)
        self.layout.addWidget(self.current_card)

        self.adjustSize()

        screen = self.screen().availableGeometry()
        target_x = screen.width() - self.width() - 40
        target_y = 40
        start_y = target_y + 20

        self.move(target_x, start_y)
        self.show()

        self.fade_anim.setStartValue(0.0)
        self.fade_anim.setEndValue(1.0)
        self.slide_anim.setStartValue(QPoint(target_x, start_y))
        self.slide_anim.setEndValue(QPoint(target_x, target_y))

        if self.slide_anim not in [self.anim_group.animationAt(i) for i in range(self.anim_group.animationCount())]:
            self.anim_group.addAnimation(self.slide_anim)

        self.anim_group.start()

    def interrupt_card(self, parsed_data, duration_ms):
        """Crossfades the current card into a new card."""
        if self.windowOpacity() == 0.0:
            self.display_card(parsed_data, duration_ms)
            return

        self.next_card_data = (parsed_data, duration_ms)
        self._start_fade_out()

    def force_finish(self):
        """Instantly begins hiding the card. Discards any pending crossfades."""
        self.next_card_data = None
        self._start_fade_out()

    def _start_fade_out(self):
        # Stop timers and active animations gracefully
        self.hold_timer.stop()
        self.anim_group.stop()

        # We only want to fade out, no sliding down
        self.anim_group.removeAnimation(self.slide_anim)

        # Fade from current opacity to 0
        self.fade_anim.setStartValue(self.windowOpacity())
        self.fade_anim.setEndValue(0.0)
        self.anim_group.start()

    def _on_animation_finished(self):
        if self.windowOpacity() == 1.0:
            self.hold_timer.start(self.current_duration)
        elif self.windowOpacity() == 0.0:
            self.hide()
            if self.next_card_data:
                # Execute the crossfade
                data, dur = self.next_card_data
                self.next_card_data = None
                self.display_card(data, dur)
            else:
                # Notify the manager the screen is empty
                self.overlay_freed.emit()