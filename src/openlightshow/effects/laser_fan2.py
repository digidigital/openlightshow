# src/openlightshow/effects/laser_fan2.py
from PySide6.QtCore import QSize, QPointF, Qt
from PySide6.QtGui import QPainter, QColor, QBrush
from ..effect_base import Effect
import math
import time


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def ease_out_cubic(t: float) -> float:
    t = clamp(t, 0.0, 1.0)
    return 1 - pow(1 - t, 3)


class LaserFan2(Effect):
    """LaserFan2 effect: two vertical columns of neon-blue discs at left and right borders
    that slide to the vertical center on beat and return on the next beat.
    """

    name: str = "LaserFan2"
    effect_class: str = "laser_fan_2"

    def __init__(self, size: QSize):
        super().__init__(size)
        self.size = size

        # Visual layout
        self.count = 12
        self.diameter = 20.0  # px (visible disc diameter)
        self.margin = 10.0  # px from screen border

        # Positions (y centers)
        self.orig_positions_left = []
        self.orig_positions_right = []
        self.left_x = 0.0
        self.right_x = 0.0
        self.center_y = 0.0
        self._recalc_positions()

        # Animation state
        self.move_to_center = False
        self.movement_progress = 1.0  # 0..1
        self.move_duration_ms = 180
        self.last_beat_time = 0.0
        self.beat_debounce_ms = 200  # ms

        # Flash/pulse state
        self.flash_alpha = 0.0
        self.flash_decay_per_ms = 0.0025

        # Color (neon blue)
        self.hue = 0.58
        self.sat = 0.95
        self.base_val = 0.9

        # store last energies for subtle effects
        self.last_low = 0.0
        self.last_mid = 0.0
        self.last_high = 0.0

    def _recalc_positions(self):
        h = max(1.0, float(self.size.height()))
        w = max(1.0, float(self.size.width()))

        # compute x positions for left and right columns (center of discs)
        self.left_x = self.margin + self.diameter / 2.0
        self.right_x = w - self.margin - self.diameter / 2.0

        # compute y centers range so discs are fully visible within margin
        min_center = self.margin + self.diameter / 2.0
        max_center = h - self.margin - self.diameter / 2.0
        if max_center < min_center:
            # fallback to single center if canvas too small
            min_center = max_center = h / 2.0

        usable_h = max(0.0, max_center - min_center)
        if self.count > 1:
            step = usable_h / (self.count - 1)
        else:
            step = 0.0

        self.orig_positions_left = [min_center + i * step for i in range(self.count)]
        self.orig_positions_right = list(self.orig_positions_left)
        self.center_y = h / 2.0

    def resize(self, size: QSize):
        super().resize(size)
        self.size = size
        self._recalc_positions()

    def update(self, dt_ms: int, energies: dict,
               sensitivity: float, flash_thresh: float):
        """
        energies: {'low': 0.0-1.0, 'mid': 0.0-1.0, 'high': 0.0-1.0}
        sensitivity: 0.0-1.0
        flash_thresh: 0.0-1.0
        """
        # clamp inputs
        low = clamp(float(energies.get('low', 0.0)), 0.0, 1.0)
        mid = clamp(float(energies.get('mid', 0.0)), 0.0, 1.0)
        high = clamp(float(energies.get('high', 0.0)), 0.0, 1.0)
        sensitivity = clamp(float(sensitivity), 0.0, 1.0)
        flash_thresh = clamp(float(flash_thresh), 0.0, 1.0)

        # store for paint-time subtle effects
        self.last_low = low
        self.last_mid = mid
        self.last_high = high

        # Progress movement animation
        if self.movement_progress < 1.0:
            self.movement_progress += (dt_ms / max(1.0, self.move_duration_ms))
            if self.movement_progress >= 1.0:
                self.movement_progress = 1.0

        # Flash triggered by mid energy crossing threshold
        if mid * sensitivity >= flash_thresh and mid > 0.01:
            self.flash_alpha = clamp(self.flash_alpha + mid * 0.9, 0.0, 1.0)

        # decay flash
        if self.flash_alpha > 0.0:
            self.flash_alpha = clamp(self.flash_alpha - self.flash_decay_per_ms * dt_ms, 0.0, 1.0)

        # subtle vertical sway based on low frequency
        self._sway = math.sin(time.time() * 2.0) * (low * sensitivity * 6.0)

    def paint(self, painter: QPainter, brightness: float):
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)

        brightness = clamp(float(brightness), 0.1, 2.0)
        t = ease_out_cubic(self.movement_progress)

        # keep discs fixed at 20px base, allow tiny pulse from flash
        pulse_scale = 1.0 + (self.flash_alpha * 0.12)
        radius = clamp(self.diameter * pulse_scale, 2.0, max(self.size.width(), self.size.height()))

        # color base value modulated by brightness and flash
        base_v = clamp(self.base_val * (0.75 + 0.25 * (1.0 - self.flash_alpha)) * brightness, 0.0, 1.0)

        # Left column
        for i, orig_y in enumerate(self.orig_positions_left):
            if self.move_to_center:
                cur_y = orig_y + (self.center_y - orig_y) * t
            else:
                cur_y = self.center_y + (orig_y - self.center_y) * t

            # subtle sway to avoid perfectly static columns
            cur_y += math.sin((i + 1) * 0.25 + time.time() * 3.0) * (self._sway * 0.02)

            # shimmer from high frequencies
            shimmer = 0.03 * math.sin(time.time() * 20.0 + i)
            v = clamp(base_v + shimmer, 0.0, 1.0)

            color = QColor.fromHsvF(self.hue, self.sat, v)
            painter.setBrush(QBrush(color))

            # draw disc centered at (left_x, cur_y)
            painter.drawEllipse(QPointF(self.left_x - radius / 2.0, cur_y - radius / 2.0),
                                radius / 2.0, radius / 2.0)

        # Right column
        for i, orig_y in enumerate(self.orig_positions_right):
            if self.move_to_center:
                cur_y = orig_y + (self.center_y - orig_y) * t
            else:
                cur_y = self.center_y + (orig_y - self.center_y) * t

            cur_y += math.cos((i + 1) * 0.28 + time.time() * 2.5) * (self._sway * 0.02)

            shimmer = 0.03 * math.cos(time.time() * 18.0 + i)
            v = clamp(base_v + shimmer, 0.0, 1.0)

            color = QColor.fromHsvF(self.hue, self.sat, v)
            painter.setBrush(QBrush(color))

            painter.drawEllipse(QPointF(self.right_x - radius / 2.0, cur_y - radius / 2.0),
                                radius / 2.0, radius / 2.0)

        painter.restore()

    def on_beat(self):
        now_ms = time.time() * 1000.0
        if (now_ms - self.last_beat_time) < self.beat_debounce_ms:
            return

        self.last_beat_time = now_ms
        self.move_to_center = not self.move_to_center
        self.movement_progress = 0.0
        super().on_beat()
