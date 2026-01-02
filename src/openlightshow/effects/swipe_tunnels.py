from PySide6.QtCore import QPointF
from PySide6.QtCore import QSize
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtGui import QPainter, QColor
from PySide6.QtGui import QPen
from ..effect_base import Effect
import random


class SwipeTunnels(Effect):
    """
    Six horizontally placed circle outlines.
    - Diameter = 1/6 of screen width (so they fit side by side without overlap).
    - Evenly distributed across screen width (touching edges).
    - Odd indices (1,3,5) start at bottom, even (2,4,6) at top.
    - On each beat, circles swipe to the opposite edge quickly.
    - Outline colors fade between random targets.
    """
    name = "Swipe Tunnels"
    effect_class = "centereffect_class01"

    def __init__(self, size: QSize):
        self.size = size
        self.n = 6
        self.radius = size.width() / (2.0 * self.n)  # = width/12
        self.positions = []
        self.targets = []
        self.colors = []
        self.target_colors = []
        self.swipe_duration_ms = 180
        self.swipe_acc = 0
        self._init_layout()

    def _init_layout(self):
        w = self.size.width()
        h = self.size.height()
        self.radius = w / (2.0 * self.n)  # diameter = w/6
        y_top = self.radius
        y_bot = h - self.radius
        self.positions = []
        self.targets = []
        self.colors = []
        self.target_colors = []

        # Centers spaced so circles exactly fill width
        self.x_positions = [(2 * i + 1) * self.radius for i in range(self.n)]

        for i in range(self.n):
            start_y = y_bot if (i % 2 == 0) else y_top
            target_y = y_top if start_y == y_bot else y_bot
            self.positions.append(start_y)
            self.targets.append(target_y)
            c = QColor.fromHsv(random.randint(0, 359), random.randint(128, 255), 255)
            self.colors.append(c)
            tc = QColor.fromHsv(random.randint(0, 359), random.randint(128, 255), 255)
            self.target_colors.append(tc)
        self.swipe_acc = 0

    def resize(self, size: QSize):
        self.size = size
        self._init_layout()

    def on_beat(self):
        h = self.size.height()
        y_top = self.radius
        y_bot = h - self.radius
        for i in range(self.n):
            self.targets[i] = y_top if self.positions[i] >= (h / 2.0) else y_bot
            self.target_colors[i] = QColor.fromHsv(random.randint(0, 359), random.randint(128, 255), 255)
        self.swipe_acc = 0

    def update(self, dt_ms: int, energies, sensitivity: float, strobe_thresh: float):
        self.swipe_acc = min(self.swipe_duration_ms, self.swipe_acc + dt_ms)
        t = self.swipe_acc / float(self.swipe_duration_ms) if self.swipe_duration_ms > 0 else 1.0
        t = max(0.0, min(1.0, t))
        for i in range(self.n):
            self.positions[i] = (1 - t) * self.positions[i] + t * self.targets[i]
            sc = self.colors[i]
            tc = self.target_colors[i]
            r = int((1 - t) * sc.red() + t * tc.red())
            g = int((1 - t) * sc.green() + t * tc.green())
            b = int((1 - t) * sc.blue() + t * tc.blue())
            self.colors[i] = QColor(r, g, b)

    def paint(self, p: QPainter, brightness: float):
        p.save()
        p.setBrush(Qt.NoBrush)  # outlines only
        for i in range(self.n):
            cx = self.x_positions[i]
            cy = self.positions[i]
            c = QColor(self.colors[i])
            c.setAlphaF(max(0.0, min(1.0, brightness)))
            pen = QPen(c, 3)
            pen.setCapStyle(Qt.RoundCap)
            p.setPen(pen)
            p.drawEllipse(QPointF(cx, cy), self.radius, self.radius)
        p.restore()
