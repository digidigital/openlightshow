import time
import random
from PySide6.QtCore import QRectF, QSize
from PySide6.QtGui import QPainter, QColor, QPen
from ..effect_base import Effect


class RectangularTunnel(Effect):
    """
    Rectangular Tunnel Effect:
    - Rectangle that grows and shrinks based on bass energy
    - Size resets randomly on beats with debouncing
    - 200ms beat debounce to prevent over-sensitivity
    """

    name = "Rectangular tunnel"
    effect_class = "centereffect_class04"

    def __init__(self, size):
        super().__init__(size)
        self.size_factor = 0.95

        # Beat debounce
        self.last_beat_time = 0.0
        self.beat_debounce_ms = 200

    def on_beat(self):
        # Debounce: ignore beats too close together
        now = time.time()
        if (now - self.last_beat_time) * 1000.0 < self.beat_debounce_ms:
            return

        self.last_beat_time = now

        super().on_beat()
        self.size_factor = random.uniform(0.1, 0.95)

    def update(self, dt, e, s, th):
        self.size_factor *= 1.0 + 0.01 * (e.get('low', 0.0) - 0.5)
        self.size_factor = max(0.05, min(self.size_factor, 0.98))

    def paint(self, p, b):
        p.save()
        w, h = self.size.width(), self.size.height()
        rw = w * self.size_factor
        rh = h * self.size_factor
        p.setPen(QPen(self.color, max(1.0, 3 * b)))
        p.drawRect(QRectF(w / 2 - rw / 2, h / 2 - rh / 2, rw, rh))
        p.restore()