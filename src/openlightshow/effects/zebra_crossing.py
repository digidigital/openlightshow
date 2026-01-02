from PySide6.QtCore import QSize
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtGui import QPainter, QColor
from PySide6.QtGui import QPen
from ..effect_base import Effect


class ZebraCrossing(Effect):
    """
    A dark grey horizontal line across the screen center with alternating white segments.
    - Each white segment is 1/8 of the screen width.
    - On each beat, the pattern shifts by half a segment length (white ↔ gap).
    """
    name = "Zebra Crossing"
    effect_class = "centereffect_class02"

    def __init__(self, size: QSize):
        self.size = size
        self.segment_len = max(1, size.width() // 8)
        self.offset = 0
        self.toggle = False

    def resize(self, size: QSize):
        self.size = size
        self.segment_len = max(1, size.width() // 8)

    def on_beat(self):
        # Toggle offset between 0 and half a segment length
        self.toggle = not self.toggle
        self.offset = 0 if not self.toggle else self.segment_len

    def update(self, dt_ms: int, energies, sensitivity: float, strobe_thresh: float):
        # No continuous updates — pattern only changes on beat
        pass

    def paint(self, p: QPainter, brightness: float):
        p.save()
        w = self.size.width()
        h = self.size.height()
        y = h // 2

        # Base dark grey line
        base_color = QColor(64, 64, 64)
        base_color.setAlphaF(max(0.0, min(1.0, 0.6 * brightness)))
        pen = QPen(base_color, 4)
        pen.setCapStyle(Qt.FlatCap)
        p.setPen(pen)
        p.drawLine(0, y, w, y)

        # White segments overlay
        seg_color = QColor(255, 255, 255)
        seg_color.setAlphaF(max(0.0, min(1.0, brightness)))
        p.setPen(QPen(seg_color, 4))

        x = -self.offset
        while x < w:
            x0 = max(0, x)
            x1 = min(w, x + self.segment_len)
            if x1 > x0:
                p.drawLine(x0, y, x1, y)
            x += 2 * self.segment_len  # alternate white and gap
        p.restore()
