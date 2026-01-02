from PySide6.QtCore import QSize
from PySide6.QtGui import QColor
from PySide6.QtGui import QPainter, QColor
from PySide6.QtGui import QPen
from ..effect_base import Effect
import math


class XRotator(Effect):
    """
    XRotator:
    Draws two perpendicular lines forming a rotating cross centered on the screen.
    - Constant rotation speed.
    - Exactly 16 beats per full rotation (constant virtual beat timing).
    - Color hue shifts based on mid-frequency energy.
    - No other reactions to the music.
    """

    name = "XRotator"
    effect_class = "centereffect_class01"

    def __init__(self, size: QSize):
        super().__init__(size)
        self.angle = 0.0
        self.hue = 0.0

        # Define a constant "virtual beat" duration (ms)
        self.virtual_beat_ms = 500.0  # 120 BPM equivalent, but fixed

        # Angular velocity:
        # 16 beats per rotation → 2π / 16 per beat
        # Convert to radians per millisecond
        self.angular_velocity = (2 * math.pi / 8.0) / self.virtual_beat_ms

    def on_beat(self):
        # No rotation change on beat — rotation is constant
        super().on_beat()

    def update(self, dt_ms: int, energies, sensitivity: float, strobe_thresh: float):
        # Constant rotation
        self.angle = (self.angle + self.angular_velocity * dt_ms) % (2 * math.pi)

        # Color driven only by mid frequencies
        mid = energies.get("mid", 0.0)
        self.hue = (self.hue + mid * 0.02) % 1.0

    def paint(self, p: QPainter, brightness: float):
        w = self.size.width()
        h = self.size.height()
        if w <= 0 or h <= 0 or brightness <= 0.0:
            return

        p.save()
        cx, cy = w / 2.0, h / 2.0
        L = math.hypot(w, h)

        color = QColor.fromHsvF(self.hue, 1.0, max(0.0, min(1.0, brightness)))
        p.setPen(QPen(color, max(2.0, 4.0 * brightness)))

        # First line
        cos_a = math.cos(self.angle)
        sin_a = math.sin(self.angle)
        p.drawLine(
            int(cx - cos_a * L), int(cy - sin_a * L),
            int(cx + cos_a * L), int(cy + sin_a * L)
        )

        # Second line (90° offset)
        a2 = self.angle + math.pi / 2.0
        cos_a2 = math.cos(a2)
        sin_a2 = math.sin(a2)
        p.drawLine(
            int(cx - cos_a2 * L), int(cy - sin_a2 * L),
            int(cx + cos_a2 * L), int(cy + sin_a2 * L)
        )
        p.restore()
