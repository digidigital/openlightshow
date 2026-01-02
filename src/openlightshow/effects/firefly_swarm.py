import random
import math
from typing import Dict

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPainter, QColor

from ..effect_base import Effect


class FireflySwarm(Effect):
    """
    FireflySwarm:
    - 100 drifting fireflies.
    - Each has a glow phase and velocity.
    - On each beat: outward scatter impulse.
    - Glow pulses smoothly.
    """

    name = "FireflySwarm"
    effect_class = "particle_class01"

    def __init__(self, size: QSize):
        super().__init__(size)
        self.num = 100
        self.fireflies = []
        self._init_fireflies()

    def _init_fireflies(self):
        w, h = self.size.width(), self.size.height()
        self.fireflies = []
        for _ in range(self.num):
            x = random.uniform(0, w)
            y = random.uniform(0, h)
            vx = random.uniform(-20, 20)
            vy = random.uniform(-20, 20)
            phase = random.uniform(0, 2 * math.pi)
            self.fireflies.append([x, y, vx, vy, phase])

    def resize(self, size: QSize):
        super().resize(size)
        self._init_fireflies()

    def on_beat(self):
        super().on_beat()
        # Scatter impulse
        for f in self.fireflies:
            angle = random.uniform(0, 2 * math.pi)
            impulse = random.uniform(40, 80)
            f[2] += math.cos(angle) * impulse
            f[3] += math.sin(angle) * impulse

    def update(self, dt_ms, energies, sensitivity, strobe_thresh):
        dt = dt_ms / 1000.0
        w, h = self.size.width(), self.size.height()

        for f in self.fireflies:
            x, y, vx, vy, phase = f

            # Update position
            x += vx * dt
            y += vy * dt

            # Wrap around screen
            if x < 0: x += w
            if x >= w: x -= w
            if y < 0: y += h
            if y >= h: y -= h

            # Slow down velocity (friction)
            vx *= 0.98
            vy *= 0.98

            # Glow phase
            phase = (phase + dt * 2.0) % (2 * math.pi)

            f[0], f[1], f[2], f[3], f[4] = x, y, vx, vy, phase

    def paint(self, p: QPainter, brightness: float):
        if brightness <= 0:
            return

        p.save()
        p.setPen(Qt.NoPen)

        for x, y, vx, vy, phase in self.fireflies:
            glow = (math.sin(phase) * 0.5 + 0.5) * brightness
            alpha = int(80 + glow * 175)
            color = QColor(255, 255, 180, alpha)
            p.setBrush(color)
            p.drawEllipse(int(x), int(y), 6, 6)
        p.restore()
