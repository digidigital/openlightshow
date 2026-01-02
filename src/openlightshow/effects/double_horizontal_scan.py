from PySide6.QtCore import QPointF
from PySide6.QtCore import QRectF
from PySide6.QtCore import QSize
from PySide6.QtGui import QColor
from PySide6.QtGui import QPainter, QColor
from PySide6.QtGui import QPen
from ..effect_base import Effect


class DoubleHorizontalScan(Effect):
    """
    DoubleHorizontalScan:
    - Two horizontal scan lines moving in opposite directions.
    - Line A moves top → bottom → top.
    - Line B moves bottom → top → bottom.
    - Speed reacts to low-frequency energy.
    - All instance variables are stored on `self`, so multiple instances
      can run simultaneously without interfering with each other.
    """

    name = "Double horizontal scan lines"
    effect_class = "centereffect_class05"

    def __init__(self, size: QSize):
        super().__init__(size)
        # Each instance has its own independent state
        self.pos = 0.0      # normalized 0..1
        self.dir = 1        # +1 or -1

    def update(self, dt, energies, sensitivity, strobe_thresh):
        # Speed reacts to low frequencies, same formula as original
        speed = 0.00015 + 0.00025 * energies.get('low', 0.0)
        self.pos += self.dir * dt * speed

        # Bounce at edges
        if self.pos >= 1.0:
            self.pos = 1.0
            self.dir = -1
        elif self.pos <= 0.0:
            self.pos = 0.0
            self.dir = 1

    def paint(self, p: QPainter, brightness: float):
        p.save()

        w = self.size.width()
        h = self.size.height()

        # Line A: top → bottom
        y1 = int(self.pos * h)

        # Line B: bottom → top (mirrored)
        y2 = int((1.0 - self.pos) * h)

        pen = QPen(self.color, max(1.0, 2 * brightness))
        p.setPen(pen)

        p.drawLine(0, y1, w, y1)
        p.drawLine(0, y2, w, y2)

        p.restore()

import time
import math
import random
from PySide6.QtCore import QSize, QPointF, QRectF
from PySide6.QtGui import QColor, QPen, QPainter
