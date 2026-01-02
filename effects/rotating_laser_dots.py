from PySide6.QtCore import QPointF
from PySide6.QtCore import QSize
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtGui import QPainter, QColor
from ..effect_base import Effect
import math
import random
import time


class RotatingLaserDots(Effect):
    """
    Rotating Laser Dots effect:
    - A ring of 10px dots orbiting around the screen center.
    - All dots share the same color, which changes randomly
      according to the music energies.
    - The ring radius oscillates smoothly between min and max,
      independent of music.
    - On each beat, there is a 10% chance the rotation direction reverses,
      but only if the cooldown period has elapsed.
    - Painter state is isolated with save/restore.
    """
    name = "Rotating Laser Dots"
    effect_class = "particle_class01"

    def __init__(self, size: QSize):
        super().__init__(size)
        self.size = size
        self.center = QPointF(size.width() / 2, size.height() / 2)

        self.num_dots = 24
        self.dot_radius = 5  # 10px diameter

        # ring radius oscillation
        self.min_radius = 40
        self.max_radius = min(size.width(), size.height()) / 2 - 20
        self.radius = (self.min_radius + self.max_radius) / 2
        self.radius_dir = 1
        self.radius_speed = 40  # pixels per second

        # rotation
        self.angle = 0.0
        self.rotation_speed = 0.002  # radians per ms 
        self.rotation_dir = 1

        # color
        self.color = QColor("white")

        # beat cooldown (ms)
        self.beat_cooldown = 300  # 0.3s between accepted beats
        self.last_beat_time = 0

    def resize(self, size: QSize):
        self.size = size
        self.center = QPointF(size.width() / 2, size.height() / 2)
        self.max_radius = min(size.width(), size.height()) / 2 - 20

    def on_beat(self):
        now = time.time() * 1000  # current time in ms
        if now - self.last_beat_time >= self.beat_cooldown:
            if random.random() < 0.10:  # 10% chance
                self.rotation_dir *= -1
            self.last_beat_time = now

    def update(self, dt_ms: int, energies, sensitivity: float, strobe_thresh: float):
        dt = dt_ms / 1000.0

        # update rotation
        self.angle += self.rotation_speed * dt_ms * self.rotation_dir

        # update radius oscillation
        self.radius += self.radius_dir * self.radius_speed * dt
        if self.radius >= self.max_radius:
            self.radius = self.max_radius
            self.radius_dir = -1
        elif self.radius <= self.min_radius:
            self.radius = self.min_radius
            self.radius_dir = 1

        # update color based on energies
        low, mid, high = energies.get("low", 0), energies.get("mid", 0), energies.get("high", 0)
        total = low + mid + high
        if total > 0:
            r = random.random() * total
            if r < low:
                self.color = QColor("red")
            elif r < low + mid:
                self.color = QColor("green")
            else:
                self.color = QColor("blue")

    def paint(self, p: QPainter, brightness: float):
        p.save()
        p.setRenderHint(QPainter.Antialiasing, True)

        c = QColor(self.color)
        c.setAlphaF(max(0.0, min(1.0, brightness)))
        p.setBrush(c)
        p.setPen(Qt.NoPen)

        for i in range(self.num_dots):
            theta = self.angle + (2 * math.pi * i / self.num_dots)
            x = self.center.x() + self.radius * math.cos(theta)
            y = self.center.y() + self.radius * math.sin(theta)
            p.drawEllipse(QPointF(x, y), self.dot_radius, self.dot_radius)

        p.restore()
