from PySide6.QtCore import QSize
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtGui import QPainter, QColor
from ..effect_base import Effect
import random


class FlashyDots(Effect):
    """
    FlashyDots:
    - Shows 50 small dots scattered randomly across the screen.
    - On each beat:
        * All dots jump to new random positions.
        * A new random color is chosen.
        * Dots flash brightly, then fade out.
    - No other reactions to music.
    """

    name = "FlashyDots"
    effect_class = "particle_class01"

    def __init__(self, size: QSize):
        super().__init__(size)
        self.num_dots = 50
        self.positions = []
        self.color = QColor(255, 255, 255)
        self.flash_strength = 0.0  # fades after beat
        self._randomize_positions()

    def _randomize_positions(self):
        w = self.size.width()
        h = self.size.height()
        self.positions = [
            (random.randint(0, w - 1), random.randint(0, h - 1))
            for _ in range(self.num_dots)
        ]

    def resize(self, size: QSize):
        super().resize(size)
        self._randomize_positions()

    def on_beat(self):
        super().on_beat()
        self._randomize_positions()

        # Random color on each flash
        self.color = QColor(
            random.randint(50, 255),
            random.randint(50, 255),
            random.randint(50, 255)
        )

        # Flash intensity
        self.flash_strength = 1.0

    def update(self, dt_ms: int, energies, sensitivity: float, strobe_thresh: float):
        # Fade flash over time
        fade_speed = 0.0025  # lower = slower fade
        self.flash_strength = max(0.0, self.flash_strength - fade_speed * dt_ms)

    def paint(self, p: QPainter, brightness: float):
        if brightness <= 0.0:
            return

        # Dot brightness depends on flash strength (clamped to valid range)
        alpha = int(min(255, 255 * self.flash_strength * brightness))
        if alpha <= 0:
            return

        p.save()
        dot_color = QColor(self.color)
        dot_color.setAlpha(alpha)
        p.setPen(Qt.NoPen)
        p.setBrush(dot_color)

        for (x, y) in self.positions:
            p.drawEllipse(x, y, 6, 6)  # small dots
        p.restore()
