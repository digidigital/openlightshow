from PySide6.QtCore import QPointF
from PySide6.QtCore import QRectF
from PySide6.QtCore import QSize
from PySide6.QtGui import QPainter, QColor
from PySide6.QtGui import QPen
from ..effect_base import Effect
import math
import random


class Flowers(Effect):
    name = "Flowers"
    effect_class = "centereffect_class03"

    def __init__(self, size: QSize):
        super().__init__(size)
        self.n = 6
        self.circles = []
        self._initialized = False
        self._last_size = QSize(0, 0)
        # Do not place circles yet if size isn’t reliable
        # They’ll be initialized in resize() or the first update()

    def resize(self, size: QSize):
        # Update size and reinitialize with correct canvas bounds
        self.size = size
        if size.width() > 0 and size.height() > 0:
            self._init_fixed_positions()
            self._initialized = True
            self._last_size = QSize(size.width(), size.height())

    def _ensure_initialized(self):
        # Lazy init in case the effect was constructed before the widget had a proper size
        if not self._initialized:
            w, h = self.size.width(), self.size.height()
            if w > 0 and h > 0:
                self._init_fixed_positions()
                self._initialized = True
                self._last_size = QSize(w, h)

    def _init_fixed_positions(self):
        """Place circles in 4 corners, 1 center, and 1 random position using current canvas size."""
        self.circles.clear()
        w, h = float(self.size.width()), float(self.size.height())
        if w <= 0 or h <= 0:
            return  # wait for a valid size

        # Radius scaled to canvas; keep inside bounds
        max_r = min(w, h) / 6.0
        corner_r = max(24.0, max_r * 0.7)  # slightly smaller in corners
        center_r = max(24.0, max_r * 0.9)
        rand_r = random.uniform(30.0, max_r)

        positions = [
            QPointF(corner_r, corner_r),             # top-left
            QPointF(w - corner_r, corner_r),         # top-right
            QPointF(corner_r, h - corner_r),         # bottom-left
            QPointF(w - corner_r, h - corner_r),     # bottom-right
            QPointF(w * 0.5, h * 0.5),               # center
            QPointF(random.uniform(rand_r, w - rand_r),
                    random.uniform(rand_r, h - rand_r))  # random
        ]

        radii = [corner_r, corner_r, corner_r, corner_r, center_r, rand_r]

        for pos, r in zip(positions, radii):
            v = QPointF(random.uniform(-60, 60), random.uniform(-60, 60))
            self.circles.append((pos, r, v))

    def on_beat(self):
        super().on_beat()
        self._ensure_initialized()
        # Small organic variation on beat
        for i in range(len(self.circles)):
            c, r, v = self.circles[i]
            v = QPointF(v.x() + random.uniform(-40, 40),
                        v.y() + random.uniform(-40, 40))
            r = max(20.0, min(r * random.uniform(0.95, 1.05),
                              min(self.size.width(), self.size.height()) / 5.0))
            self.circles[i] = (c, r, v)

    def update(self, dt_ms, e, s, th):
        self._ensure_initialized()

        # If canvas size changes during runtime, reinitialize to cover full area
        if self.size.width() != self._last_size.width() or self.size.height() != self._last_size.height():
            self._init_fixed_positions()
            self._last_size = QSize(self.size.width(), self.size.height())

        dt = dt_ms / 1000.0
        w, h = float(self.size.width()), float(self.size.height())
        speed_scale = 0.2 + s * e.get('mid', 0.0)

        new = []
        for c, r, v in self.circles:
            nx = c.x() + v.x() * dt * speed_scale
            ny = c.y() + v.y() * dt * speed_scale

            # Keep circles fully inside the canvas
            if nx - r < 0.0:
                nx = r; v.setX(abs(v.x()))
            if nx + r > w:
                nx = w - r; v.setX(-abs(v.x()))
            if ny - r < 0.0:
                ny = r; v.setY(abs(v.y()))
            if ny + r > h:
                ny = h - r; v.setY(-abs(v.y()))

            new.append((QPointF(nx, ny), r, v))

        # Simple overlap resolution
        for i in range(len(new)):
            ci, ri, vi = new[i]
            for j in range(i + 1, len(new)):
                cj, rj, vj = new[j]
                dx, dy = cj.x() - ci.x(), cj.y() - ci.y()
                d2 = dx * dx + dy * dy
                min_d = ri + rj + 2.0
                if d2 < min_d * min_d and d2 > 1e-6:
                    d = math.sqrt(d2)
                    overlap = min_d - d
                    ux, uy = dx / d, dy / d
                    ci = QPointF(ci.x() - ux * overlap * 0.5, ci.y() - uy * overlap * 0.5)
                    cj = QPointF(cj.x() + ux * overlap * 0.5, cj.y() + uy * overlap * 0.5)
                    vi = QPointF(vi.x() - ux * 10.0, vi.y() - uy * 10.0)
                    vj = QPointF(vj.x() + ux * 10.0, vj.y() + uy * 10.0)
                    new[i] = (ci, ri, vi)
                    new[j] = (cj, rj, vj)

        self.circles = new

    def paint(self, p, b):
        p.save()
        self._ensure_initialized()
        p.setPen(QPen(self.color, max(1.0, 2.0 * b)))
        for c, r, _ in self.circles:
            p.drawEllipse(QRectF(c.x() - r, c.y() - r, 2.0 * r, 2.0 * r))
        p.restore()
