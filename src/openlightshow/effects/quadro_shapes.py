from PySide6.QtCore import QPointF
from PySide6.QtCore import QSize
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtGui import QPainter, QColor
from PySide6.QtGui import QPen
from ..effect_base import Effect
import math
import random
import time


class QuadroShapes(Effect):
    """
    QuadroShapes Effect:
    - Screen divided into 4 quadrants.
    - On each beat, randomly selects one quadrant (different from the last) and one shape (circle, square, triangle).
    - Only one shape is visible at a time.
    - Square is the largest; circle and triangle are sized relative to the square.
    - Triangle baseline length equals the square's side length.
    - Shape color changes with beat and is influenced by frequency energies.
    - Includes a stricter filter to avoid too-frequent random changes.
    """

    name = "Quadro Shapes"
    effect_class = "centereffect_class03"

    def __init__(self, size: QSize):
        super().__init__(size)
        self.size = size
        self.current_quadrant = 0
        self.last_quadrant = -1
        self.current_shape = "square"
        self.color = QColor(255, 255, 255)
        self.time_since_last_change = 0
        self.min_change_interval = 300  # ms filter to prevent ghost changes

    def resize(self, size: QSize):
        self.size = size

    def on_beat(self):
        if self.time_since_last_change >= self.min_change_interval:
            available_quadrants = [q for q in range(4) if q != self.current_quadrant]
            self.last_quadrant = self.current_quadrant
            self.current_quadrant = random.choice(available_quadrants)
            self.current_shape = random.choice(["circle", "square", "triangle"])
            self.time_since_last_change = 0

    def update(self, dt_ms: int, energies, sensitivity: float, strobe_thresh: float):
        self.time_since_last_change += dt_ms
        r = int(255 * min(1.0, energies.get("low", 0.0) * sensitivity))
        g = int(255 * min(1.0, energies.get("mid", 0.0) * sensitivity))
        b = int(255 * min(1.0, energies.get("high", 0.0) * sensitivity))
        self.color = QColor(r, g, b)

    def paint(self, p: QPainter, brightness: float):
        if self.size.width() <= 0 or self.size.height() <= 0:
            return

        p.save()
        p.setRenderHint(QPainter.Antialiasing, True)

        pen = QPen(self.color)
        pen.setWidth(3)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)

        w = self.size.width() // 2
        h = self.size.height() // 2

        centers = [
            QPointF(w / 2, h / 2),             # top-left
            QPointF(w + w / 2, h / 2),         # top-right
            QPointF(w / 2, h + h / 2),         # bottom-left
            QPointF(w + w / 2, h + h / 2),     # bottom-right
        ]

        center = centers[self.current_quadrant]
        # Square side fills most of the quadrant
        side = min(w, h) * 0.95
        half_side = side / 2
        rect_x = center.x() - half_side
        rect_y = center.y() - half_side

        if self.current_shape == "square":
            p.drawRect(rect_x, rect_y, side, side)

        elif self.current_shape == "circle":
            # Circle inscribed in square
            radius = half_side
            p.drawEllipse(center, radius, radius)

        elif self.current_shape == "triangle":
            # Equilateral triangle with baseline = square side
            # Baseline centered horizontally at bottom of square
            x1 = center.x() - half_side
            y1 = center.y() + half_side
            x2 = center.x() + half_side
            y2 = center.y() + half_side
            # Height of equilateral triangle
            height = (math.sqrt(3) / 2) * side
            x3 = center.x()
            y3 = center.y() + half_side - height
            points = [QPointF(x1, y1), QPointF(x2, y2), QPointF(x3, y3)]
            p.drawPolygon(points)

        p.restore()
