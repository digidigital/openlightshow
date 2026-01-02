from PySide6.QtCore import QPointF
from PySide6.QtCore import QRectF
from PySide6.QtCore import QSize
from PySide6.QtGui import QColor
from PySide6.QtGui import QPainter, QColor
from PySide6.QtGui import QPen
from ..effect_base import Effect
import math
import time


class DuoTunnel(Effect):
    """
    Two circular arcs that orbit around the center of the screen.
    - Both circles spin around the screen center in opposite directions.
    - Arc rotation speed reacts to high-frequency energy.
    - On each valid beat, they get a 5° kick.
    - Beat filter prevents multiple triggers from rapid beat detections.
    """
    name = "Duo tunnel"
    effect_class = "centereffect_class06"

    def __init__(self, size: QSize):
        super().__init__(size)
        self.angle = 0.0
        self.color = QColor(255, 255, 255)

        # Kick state
        self.kick_angle = 0.0
        self.kick_decay_ms = 300
        self.kick_time_left = 0

        # Beat filter
        self.last_trigger_ms = 0
        self.min_interval_ms = 250  # ignore beats faster than this

    def on_beat(self):
        now = int(time.time() * 1000)
        if now - self.last_trigger_ms < self.min_interval_ms:
            return  # ignore too-frequent beats
        self.last_trigger_ms = now

        # Apply a 5° kick (in radians)
        self.kick_angle = math.radians(5)
        self.kick_time_left = self.kick_decay_ms

    def update(self, dt_ms: int, energies, sensitivity: float, strobe_thresh: float):
        # Base angular speed from high frequencies
        speed = 0.5 + energies.get('high', 0.0) * sensitivity * 2.0
        extra = self.kick_angle if self.kick_time_left > 0 else 0.0
        self.angle += (dt_ms / 1000.0) * speed + extra
        self.angle %= 2 * math.pi

        # Decay the kick
        if self.kick_time_left > 0:
            self.kick_time_left = max(0, self.kick_time_left - dt_ms)
            if self.kick_time_left == 0:
                self.kick_angle = 0.0

        # Color from mid frequencies
        hue = int(energies.get('mid', 0.0) * 359)
        sat = 200
        val = 255
        self.color = QColor.fromHsv(hue, sat, val)

    def paint(self, p: QPainter, brightness: float):
        p.save()
        w, h = self.size.width(), self.size.height()
        cx, cy = w / 2.0, h / 2.0
        orbit_radius = min(w, h) / 4.0
        circle_radius = min(w, h) / 6.0

        # Orbiting centers
        c1 = QPointF(cx + orbit_radius * math.cos(self.angle),
                     cy + orbit_radius * math.sin(self.angle))
        c2 = QPointF(cx + orbit_radius * math.cos(self.angle + math.pi),
                     cy + orbit_radius * math.sin(self.angle + math.pi))

        # Arc parameters
        gap_deg = 360.0 * (10.0 / (2.0 * math.pi * circle_radius))
        start_deg = math.degrees(self.angle)
        span_deg = 360.0 - gap_deg

        # Pen
        c = QColor(self.color)
        c.setAlphaF(max(0.0, min(1.0, brightness)))
        pen = QPen(c, max(1.0, 3 * brightness))
        p.setPen(pen)

        for center in (c1, c2):
            rect = QRectF(center.x() - circle_radius,
                          center.y() - circle_radius,
                          2 * circle_radius,
                          2 * circle_radius)
            p.drawArc(rect, int(start_deg * 16), int(span_deg * 16))
        p.restore()
