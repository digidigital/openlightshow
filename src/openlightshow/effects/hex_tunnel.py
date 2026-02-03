from PySide6.QtCore import QPointF
from PySide6.QtCore import QSize
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtGui import QPainter, QColor
from PySide6.QtGui import QPen
from ..effect_base import Effect
import math
import random


class HexTunnel(Effect):
    """
    A hexagon outline with each segment colored; colors randomize on beats.
    """
    name = "Hex Tunnel"
    effect_class = "centereffect_class03"

    def __init__(self, size: QSize):
        self.size = size
        self.colors = [QColor(255, 0, 0), QColor(255, 128, 0), QColor(255, 255, 0),
                       QColor(0, 255, 0), QColor(0, 128, 255), QColor(128, 0, 255)]

    def resize(self, size: QSize):
        self.size = size

    def on_beat(self):
        # Randomize segment colors on beat
        self.colors = [QColor.fromHsv(random.randint(0, 359), random.randint(128, 255), 255) for _ in range(6)]

    def update(self, dt_ms: int, energies, sensitivity: float, strobe_thresh: float):
        # Optional subtle brightness modulation from energies (not filling background)
        pass

    def paint(self, p: QPainter, brightness: float):
        p.save()
        w = self.size.width()
        h = self.size.height()
        cx, cy = w / 2.0, h / 2.0
        r = min(w, h) * 0.4

        verts = []
        for i in range(6):
            theta = 3.141592653589793 / 3.0 * i  # 0,60,120...
            x = cx + r * float(math.cos(theta))
            y = cy + r * float(math.sin(theta))
            verts.append(QPointF(x, y))

        # Draw edges with separate colors
        p.setBrush(Qt.NoBrush)
        for i in range(6):
            a = verts[i]
            b = verts[(i + 1) % 6]
            c = QColor(self.colors[i])
            c.setAlphaF(max(0.0, min(1.0, brightness)))
            pen = QPen(c, 3)
            pen.setCapStyle(Qt.FlatCap)
            p.setPen(pen)
            p.drawLine(a, b)
        p.restore()
