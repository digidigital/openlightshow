from PySide6.QtCore import QSize
from PySide6.QtGui import QColor
from PySide6.QtGui import QPainter, QColor
from ..effect_base import Effect
import random


class PixelRain(Effect):
    """
    PixelRain:
    - 120 tiny falling pixels.
    - Constant downward drift.
    - On each beat: temporary speed burst.
    - Pixels are always drawn at full brightness.
    """

    name = "PixelRain"
    effect_class = "particle_class01"

    def __init__(self, size: QSize):
        super().__init__(size)
        self.num_pixels = 120
        self.pixels = []
        self.base_speed = 60.0  # px/sec
        self.burst_speed = 0.0
        self.hue = 0.0
        self._init_pixels()

    def _init_pixels(self):
        w, h = self.size.width(), self.size.height()
        self.pixels = [
            [random.randint(0, w - 1), random.randint(0, h - 1)]
            for _ in range(self.num_pixels)
        ]

    def resize(self, size: QSize):
        super().resize(size)
        self._init_pixels()

    def on_beat(self):
        super().on_beat()
        self.burst_speed = 200.0  # temporary boost

    def update(self, dt_ms, energies, sensitivity, strobe_thresh):
        dt = dt_ms / 1000.0
        w, h = self.size.width(), self.size.height()

        # Fade burst speed
        self.burst_speed = max(0.0, self.burst_speed - dt * 150.0)

        # Color cycle
        self.hue = (self.hue + dt * 0.05) % 1.0

        speed = self.base_speed + self.burst_speed

        for p in self.pixels:
            p[1] += speed * dt
            if p[1] >= h:
                p[1] = 0
                p[0] = random.randint(0, w - 1)

    def paint(self, p: QPainter, brightness: float):
        p.save()
        # Always full brightness → ignore brightness parameter
        color = QColor.fromHsvF(self.hue, 1.0, 1.0)
        p.setPen(color)

        for x, y in self.pixels:
            p.drawPoint(int(x), int(y))
            p.drawPoint(int(x+1), int(y))
            p.drawPoint(int(x), int(y+1))
            p.drawPoint(int(x+1), int(y+1))
        p.restore()
