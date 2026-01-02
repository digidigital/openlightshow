from PySide6.QtCore import QPointF
from PySide6.QtCore import QSize
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtGui import QPainter, QColor
from ..effect_base import Effect
import math


class LaserPlanets(Effect):
    """
    Laser Planets effect:
    Four neon‑bright dots orbit around the screen center in eccentric
    ellipses. Each ellipse itself slowly rotates (precesses) at
    half the angular speed of its planet. Dots are drawn filled
    with no outline, so they don't interfere with other effects.
    """
    name = "Laser Planets"
    effect_class = "particle_class01"

    def __init__(self, size: QSize):
        super().__init__(size)
        self.size = size
        self.center = QPointF(size.width() / 2, size.height() / 2)

        # Neon / laser‑like colors
        self.colors = [
            QColor(255, 255, 255),   # pure white
            QColor(255, 50, 50),     # hot red
            QColor(80, 180, 255),    # electric blue
            QColor(50, 255, 120)     # neon green
        ]

        self._set_radii(size)

        self.angles = [i * (math.pi / 2) for i in range(4)]
        self.angular_vel = [0.003, 0.0024, 0.0018, 0.0015]
        self.eccentricities = [0.6, 0.8, 1.2, 1.4]
        self.orientations = [0.0, 0.0, 0.0, 0.0]

    def _set_radii(self, size: QSize):
        margin = 10
        max_rx = size.width() / 2 - margin
        max_ry = size.height() / 2 - margin
        max_radius = min(max_rx, max_ry)
        self.base_radii = [
            max_radius * 0.25,
            max_radius * 0.5,
            max_radius * 0.75,
            max_radius * 1.0,
        ]

    def resize(self, size: QSize):
        self.size = size
        self.center = QPointF(size.width() / 2, size.height() / 2)
        self._set_radii(size)

    def on_beat(self):
        pass

    def update(self, dt_ms: int, energies, sensitivity: float, strobe_thresh: float):
        for i in range(4):
            self.angles[i] += self.angular_vel[i] * dt_ms
            self.orientations[i] += (self.angular_vel[i] * 0.5) * dt_ms

    def paint(self, p: QPainter, brightness: float):
        p.save()
        p.setRenderHint(QPainter.Antialiasing, True)

        # Additive blending for glowing effect
        p.setCompositionMode(QPainter.CompositionMode_Plus)

        for i, color in enumerate(self.colors):
            r = self.base_radii[i]
            angle = self.angles[i]
            ecc = self.eccentricities[i]
            orient = self.orientations[i]

            rx, ry = r, r * ecc
            max_rx = self.size.width() / 2 - 10
            max_ry = self.size.height() / 2 - 10
            if rx > max_rx:
                scale = max_rx / rx
                rx *= scale; ry *= scale
            if ry > max_ry:
                scale = max_ry / ry
                rx *= scale; ry *= scale

            cos_o, sin_o = math.cos(orient), math.sin(orient)
            x = self.center.x() + rx * math.cos(angle) * cos_o - ry * math.sin(angle) * sin_o
            y = self.center.y() + rx * math.cos(angle) * sin_o + ry * math.sin(angle) * cos_o

            c = QColor(color)
            # Stronger alpha for more light
            c.setAlphaF(max(0.0, min(1.0, brightness * 2.5)))
            p.setBrush(c)
            p.setPen(Qt.NoPen)
            p.drawEllipse(QPointF(x, y), 2.5, 2.5)  # 5px diameter

        p.restore()
