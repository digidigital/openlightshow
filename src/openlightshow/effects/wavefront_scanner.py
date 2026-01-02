import math
from typing import Dict

from PySide6.QtCore import QSize
from PySide6.QtGui import QPainter, QColor, QPen

from ..effect_base import Effect


class WavefrontScanner(Effect):
    """
    WavefrontScanner:
    - A sweeping horizontal sine-wave line.
    - Scrolls across the screen.
    - Beats increase amplitude briefly.
    - High frequencies add jitter.
    """

    name = "WavefrontScanner"
    effect_class = "centereffect_class02"

    def __init__(self, size: QSize):
        super().__init__(size)
        self.phase = 0.0
        self.amp = 20.0
        self.amp_boost = 0.0

    def on_beat(self):
        super().on_beat()
        self.amp_boost = 25.0  # temporary amplitude boost

    def update(self, dt_ms, energies, sensitivity, strobe_thresh):
        dt = dt_ms / 1000.0

        # Scroll wave
        self.phase += dt * 2.0

        # Fade amplitude boost
        self.amp_boost = max(0.0, self.amp_boost - dt * 40.0)

        # High-frequency jitter
        jitter = energies.get("high", 0.0) * 4.0

        self.current_amp = self.amp + self.amp_boost + jitter

    def paint(self, p: QPainter, brightness: float):
        if brightness <= 0:
            return

        p.save()
        w = self.size.width()
        h = self.size.height()
        mid = h / 2

        color = QColor.fromHsvF(0.55, 1.0, max(0.0, min(1.0, brightness)))
        p.setPen(QPen(color, 2))

        # Compute first point at x=0
        last_x = 0
        last_y = mid + math.sin(self.phase + 0 * 0.02) * self.current_amp

        # Draw sine wave across the screen
        for x in range(1, w):
            y = mid + math.sin(self.phase + x * 0.02) * self.current_amp
            p.drawLine(last_x, int(last_y), x, int(y))
            last_x, last_y = x, y
        p.restore()
