from PySide6.QtCore import QSize
from PySide6.QtGui import QColor
from PySide6.QtGui import QPainter, QColor
from ..effect_base import Effect
import time


class FlashWipe(Effect):
    """
    A white bar (20px high) swiping from bottom to top across the screen.
    - Triggers every 4 valid beats (with cooldown).
    - Swipe animation lasts ~200 ms.
    - Only one bar is visible at a time.
    """
    name = "Flash wipe"
    effect_class = "flash_class01"

    def __init__(self, size: QSize):
        self.size = size
        self.bar_h = 40
        self.active = False
        self.progress = 0.0
        self.swipe_duration_ms = 200
        self.time_acc = 0

        # Beat handling
        self.beat_count = 0
        self.last_trigger_ms = 0
        self.min_interval_ms = 250  # ignore beats faster than this

    def resize(self, size: QSize):
        self.size = size

    def on_beat(self):
        now = int(time.time() * 1000)
        if now - self.last_trigger_ms < self.min_interval_ms:
            return  # ignore too-frequent beats
        self.last_trigger_ms = now

        self.beat_count += 1
        if self.beat_count % 8 == 0:  # trigger every 8th valid beat
            self.active = True
            self.progress = 0.0
            self.time_acc = 0

    def update(self, dt_ms: int, energies, sensitivity: float, strobe_thresh: float):
        if not self.active:
            return
        self.time_acc += dt_ms
        self.progress = min(1.0, self.time_acc / self.swipe_duration_ms)
        if self.progress >= 1.0:
            self.active = False

    def paint(self, p: QPainter, brightness: float):
        if not self.active:
            return
        p.save()
        w = self.size.width()
        h = self.size.height()
        # Interpolated y position
        y = h - self.bar_h - int(self.progress * h)
        color = QColor(255, 255, 255)
        color.setAlphaF(max(0.0, min(1.0, brightness)))
        p.fillRect(0, y, w, self.bar_h, color)
        p.restore()
