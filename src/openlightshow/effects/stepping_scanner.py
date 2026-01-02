from PySide6.QtCore import QSize
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtGui import QPainter, QColor
from PySide6.QtGui import QPen
from ..effect_base import Effect
import random
import time


class SteppingScanner(Effect):
    """
    A horizontal line that steps from bottom to top at four positions.
    - Only one line is drawn at a time.
    - On each beat (with cooldown), the line swipes quickly to the next position.
    - Each step changes to a new random color.
    """
    name = "Stepping scanner"
    effect_class = "centereffect_class05"

    def __init__(self, size: QSize):
        self.size = size
        self.step_idx = 0
        self.color = QColor(255, 255, 255)
        self._compute_positions()

        # Animation state
        self.animating = False
        self.anim_time = 0
        self.anim_duration = 150  # ms
        self.start_y = self.steps[0]
        self.target_y = self.steps[0]
        self.current_y = self.steps[0]

        # Beat cooldown
        self.last_trigger_ms = 0
        self.min_interval_ms = 250  # ignore beats faster than this

    def _compute_positions(self):
        h = self.size.height()
        self.steps = [h - 1, int(h * 2 / 3), int(h * 1 / 3), 1]

    def resize(self, size: QSize):
        self.size = size
        self._compute_positions()
        self.current_y = self.steps[self.step_idx]

    def on_beat(self):
        now = int(time.time() * 1000)
        if now - self.last_trigger_ms < self.min_interval_ms:
            return  # ignore too-frequent beats
        self.last_trigger_ms = now

        # Advance to next step
        old_idx = self.step_idx
        self.step_idx = (self.step_idx + 1) % len(self.steps)
        self.start_y = self.steps[old_idx]
        self.target_y = self.steps[self.step_idx]
        self.animating = True
        self.anim_time = 0

        # New color
        self.color = QColor.fromHsv(
            random.randint(0, 359),
            random.randint(128, 255),
            255
        )

    def update(self, dt_ms: int, energies, sensitivity: float, strobe_thresh: float):
        if self.animating:
            self.anim_time += dt_ms
            t = min(1.0, self.anim_time / self.anim_duration)
            # Smooth interpolation
            t_smooth = t * t * (3 - 2 * t)
            self.current_y = int((1 - t_smooth) * self.start_y + t_smooth * self.target_y)
            if t >= 1.0:
                self.animating = False
                self.current_y = self.target_y

    def paint(self, p: QPainter, brightness: float):
        p.save()
        w = self.size.width()
        y = self.current_y
        c = QColor(self.color)
        c.setAlphaF(max(0.0, min(1.0, brightness)))
        pen = QPen(c, 3)
        pen.setCapStyle(Qt.FlatCap)
        p.setPen(pen)
        p.drawLine(0, y, w, y)
        p.restore()
