from PySide6.QtCore import QPointF
from PySide6.QtCore import QSize
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtGui import QPainter, QColor
from PySide6.QtGui import QPen
from PySide6.QtGui import QPolygonF
from ..effect_base import Effect
import math


class StarTunnel(Effect):
    """
    A rotating 5-point star outline. Color responds to frequency bands.
    Rotation is significantly slower, and the beat kick effect is subtle.
    """
    name = "Star Tunnel"
    effect_class = "centereffect_class06"

    def __init__(self, size: QSize):
        self.size = size
        self.angle = 0.0
        # Much slower base rotation
        self.base_angular_speed = 0.0001  # radians per ms
        # Smaller kick
        self.kick_speed = 0.0
        self.kick_decay_ms = 400
        self.kick_time_left = 0
        self.color = QColor(255, 255, 255)

    def resize(self, size: QSize):
        self.size = size

    def on_beat(self):
        # Gentle kick
        self.kick_speed = 0.0005
        self.kick_time_left = self.kick_decay_ms

    def update(self, dt_ms: int, energies, sensitivity: float, strobe_thresh: float):
        # Rotation update with kick decay
        extra = self.kick_speed if self.kick_time_left > 0 else 0.0
        self.angle += (self.base_angular_speed * (1.0 + sensitivity) + extra) * dt_ms
        self.angle %= (2.0 * math.pi)
        if self.kick_time_left > 0:
            self.kick_time_left = max(0, self.kick_time_left - dt_ms)
            if self.kick_time_left == 0:
                self.kick_speed = 0.0

        # Color from energies
        hue = int(max(0.0, min(1.0, energies.get('high', 0.0))) * 359)
        sat = int(max(0.0, min(1.0, energies.get('mid', 0.0))) * 255)
        val = int(max(0.0, min(1.0, energies.get('low', 0.0))) * 255)
        self.color = QColor.fromHsv(hue, sat, val)

    def paint(self, p: QPainter, brightness: float):
        p.save()
        w = self.size.width()
        h = self.size.height()
        cx, cy = w / 2.0, h / 2.0

        # Fit star within smallest dimension
        outer_r = min(w, h) * 0.45
        inner_r = outer_r * 0.5
        points = []
        for i in range(10):
            r = outer_r if i % 2 == 0 else inner_r
            theta = self.angle + i * (math.pi / 5.0)
            x = cx + r * math.cos(theta)
            y = cy + r * math.sin(theta)
            points.append(QPointF(x, y))

        poly = QPolygonF(points)
        c = QColor(self.color)
        c.setAlphaF(max(0.0, min(1.0, brightness)))
        pen = QPen(c, 2)
        pen.setCapStyle(Qt.FlatCap)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        p.drawPolygon(poly)
        p.restore()
