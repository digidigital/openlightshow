from PySide6.QtCore import QSize
from PySide6.QtGui import QPainter, QColor
from PySide6.QtGui import QPen
from ..effect_base import Effect


class DoubleVerticalScan(Effect):
    """
    DoubleVerticalScan:
    - Two vertical scan lines moving in opposite directions.
    - Line A moves left → right → left.
    - Line B moves right → left → right.
    - Speed reacts to low-frequency energy.
    - All instance variables are stored on `self`, so multiple instances
      can run simultaneously without interfering with each other.
    """

    name = "Double vertical scan lines"
    effect_class = "centereffect_class05"

    def __init__(self, size: QSize):
        super().__init__(size)
        # Independent instance state
        self.pos = 0.0      # normalized 0..1
        self.dir = 1        # +1 or -1

    def update(self, dt, energies, sensitivity, strobe_thresh):
        # Same speed logic as the horizontal version
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

        # Line A: left → right
        x1 = int(self.pos * w)

        # Line B: right → left (mirrored)
        x2 = int((1.0 - self.pos) * w)

        pen = QPen(self.color, max(1.0, 2 * brightness))
        p.setPen(pen)

        p.drawLine(x1, 0, x1, h)
        p.drawLine(x2, 0, x2, h)

        p.restore()
