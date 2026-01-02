import time
import math
from PySide6.QtCore import QRectF, QSize
from PySide6.QtGui import QPainter, QColor, QPen
from ..effect_base import Effect


class BoxySensation(Effect):
    """
    Boxy Sensation Effect:
    - Pulsing rectangle that grows and shrinks from center
    - Changes color on beats with debouncing
    - 200ms beat debounce to prevent over-sensitivity
    """

    name = "Boxy sensation"
    effect_class = "centereffect_class04"

    def __init__(self, size):
        super().__init__(size)
        self.phase = 0.0
        self.speed = 0.0001

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

    def update(self, dt, e, s, th):
        self.phase += dt * self.speed
        # loop
        if self.phase > 1.0:
            self.phase = 0.0

    def paint(self, p, b):
        p.save()
        w, h = self.size.width(), self.size.height()
        scale = abs(math.sin(self.phase * math.pi))
        rw, rh = w * scale, h * scale
        p.setPen(QPen(self.color, max(1.0, 3 * b)))
        p.drawRect(QRectF(w / 2 - rw / 2, h / 2 - rh / 2, rw, rh))
        p.restore()
