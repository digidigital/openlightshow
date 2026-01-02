from PySide6.QtCore import QSize
from PySide6.QtGui import QColor
from PySide6.QtGui import QPainter, QColor
from PySide6.QtGui import QPen
from ..effect_base import Effect
import math


class SineWave(Effect):
    """
    A colorful horizontal sine wave whose amplitude/frequency react to the music bands.
    """
    name = "Sine wave"
    effect_class = "centereffect_class02"

    def __init__(self, size: QSize):
        self.size = size
        self.phase = 0.0

    def resize(self, size: QSize):
        self.size = size

    def on_beat(self):
        # Small phase kick on beat
        self.phase += 0.5

    def update(self, dt_ms: int, energies, sensitivity: float, strobe_thresh: float):
        # Amplitude from low, frequency from high, phase drift from mid
        amp_base = (self.size.height() * 0.15) * (0.3 + energies.get('low', 0.0) * sensitivity)
        self.amplitude = max(5.0, min(self.size.height() * 0.45, amp_base))
        self.frequency = 0.01 + 0.03 * energies.get('high', 0.0) * (0.5 + sensitivity * 0.5)
        self.phase += dt_ms * 0.0015 * (0.5 + energies.get('mid', 0.0))

    def paint(self, p: QPainter, brightness: float):
        p.save()
        w = self.size.width()
        h = self.size.height()
        cy = h / 2.0

        # Draw small segments with gradient-like color changes
        steps = max(100, w // 2)
        dx = w / float(steps)
        for i in range(steps):
            x0 = i * dx
            x1 = (i + 1) * dx
            y0 = cy + self.amplitude * math.sin(self.phase + self.frequency * x0)
            y1 = cy + self.amplitude * math.sin(self.phase + self.frequency * x1)
            # Color shifts across x controlled by mid energy
            hue = int((i / steps) * 359)
            sat = int(200 * (0.5 + 0.5 * max(0.0, min(1.0, brightness))))
            val = int(255 * (0.5 + 0.5 * max(0.0, min(1.0, brightness))))
            c = QColor.fromHsv(hue, sat, val)
            c.setAlphaF(max(0.0, min(1.0, brightness)))
            p.setPen(QPen(c, 2))
            p.drawLine(int(x0), int(y0), int(x1), int(y1))
        p.restore()
