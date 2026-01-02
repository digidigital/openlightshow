import random
from typing import Dict

from PySide6.QtCore import Qt, QSize, QPointF
from PySide6.QtGui import QPainter, QColor, QPen

from ..effect_base import Effect


class FlashyHoles(Effect):
    """
    FlashyHoles Effect:
    - On each beat, 8 neon-colored circles appear instantly.
    - Each circle has radius = 1/20 of screen height.
    - Each circle gets a random neon color.
    - Line thickness increases only on the beat frame (+2 px), then resets.
    - Maximum of 8 circles.
    """

    name = "FlashyHoles"
    effect_class = "centereffect_class07"

    def __init__(self, size: QSize):
        super().__init__(size)
        self.circles = []  # list of (x, y, radius, QColor)
        self.base_line_width = 2
        self.current_line_width = self.base_line_width
        self.beat_flash = False  # True only for the frame immediately after a beat

        self.neon_colors = [
            QColor(57, 255, 20),    # neon green
            QColor(199, 21, 133),   # neon purple/pink
            QColor(255, 20, 147),   # neon pink
            QColor(255, 255, 0),    # neon yellow
            QColor(255, 165, 0),    # neon orange
            QColor(0, 255, 255),    # neon cyan
            QColor(255, 0, 255),    # neon magenta
        ]

    def resize(self, size: QSize):
        super().resize(size)

    def on_beat(self):
        super().on_beat()

        w = self.size.width()
        h = self.size.height()
        r = h / 20.0

        # Mark that this frame should use boosted line width
        self.beat_flash = True
        self.current_line_width = self.base_line_width + 2

        # Add two new circles
        for _ in range(2):
            cx = random.uniform(r, w - r)
            cy = random.uniform(r, h - r)
            color = random.choice(self.neon_colors)
            self.circles.append((cx, cy, r, color))

        # Enforce max of 8 circles
        while len(self.circles) > 8:
            self.circles.pop(0)

    def update(self, dt_ms, energies, sensitivity, strobe_thresh):
        # After the beat frame, reset thickness
        if self.beat_flash:
            self.beat_flash = False
        else:
            self.current_line_width = self.base_line_width

    def paint(self, p: QPainter, brightness: float):
        p.save()

        for (cx, cy, r, color) in self.circles:
            c = QColor(color)
            c.setAlphaF(max(0.0, min(1.0, brightness)))

            pen = QPen(c, self.current_line_width)
            p.setPen(pen)
            p.setBrush(Qt.NoBrush)

            p.drawEllipse(QPointF(cx, cy), r, r)

        p.restore()
