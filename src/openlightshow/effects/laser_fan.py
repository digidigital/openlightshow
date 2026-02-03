# src/openlightshow/effects/laser_fan.py
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


class LaserFan(Effect):
    """LaserFan effect: two rows of neon-blue discs that fan to center on beat."""

    name: str = "LaserFan"
    effect_class: str = "laser_fan"

    def __init__(self, size: QSize):
        super().__init__(size)
        self.size = size

        # Visual layout
        self.count = 12
        self.diameter = 20.0  # px (visible disc diameter)
        self.margin = 10.0  # px from top/bottom and sides
        self.top_y = self.margin + self.diameter / 2.0
        self.bottom_y = max(self.margin + self.diameter / 2.0,
                            self.size.height() - self.margin - self.diameter / 2.0)

        # Positions
        self.orig_positions_top = []  # list of x positions (center)
        self.orig_positions_bottom = []
        self._recalc_positions()

        # Animation state
        self.move_to_center = False  # target state after beat
        self.movement_progress = 1.0  # 0..1 progress of current movement
        self.move_duration_ms = 180  # how fast discs move to center (ms)
        self.last_update_time = 0
        self.last_beat_time = 0.0
        self.beat_debounce_ms = 200  # debounce between beats

        # Flash/pulse state
        self.flash_alpha = 0.0
        self.flash_decay_per_ms = 0.0025  # how fast flash fades

        # Colors (neon blue base in HSV)
        self.hue = 0.58  # blue-ish
        self.sat = 0.95
        self.base_val = 0.9

    def _recalc_positions(self):
        w = max(1, self.size.width())
        # evenly distribute centers horizontally with margin to screen border
        usable_w = max(0.0, w - 2 * self.margin)
        if self.count > 1:
            step = usable_w / (self.count - 1)
        else:
            step = 0
        self.orig_positions_top = [self.margin + i * step for i in range(self.count)]
        self.orig_positions_bottom = list(self.orig_positions_top)
        self.center_x = w / 2.0

        # y positions
        self.top_y = self.margin + self.diameter / 2.0
        self.bottom_y = max(self.margin + self.diameter / 2.0,
                            self.size.height() - self.margin - self.diameter / 2.0)

    def resize(self, size: QSize):
        super().resize(size)
        self.size = size
        self._recalc_positions()

    def update(self, dt_ms: int, energies: dict,
               sensitivity: float, flash_thresh: float):
        """
        Update animation state.
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

        # Progress movement animation
        if self.movement_progress < 1.0:
            self.movement_progress += (dt_ms / max(1.0, self.move_duration_ms))
            if self.movement_progress >= 1.0:
                self.movement_progress = 1.0

        # Flash triggered by strong mid energy crossing threshold
        if mid * sensitivity >= flash_thresh and mid > 0.01:
            # create a quick flash proportional to mid energy
            self.flash_alpha = clamp(self.flash_alpha + mid * 0.9, 0.0, 1.0)

        # decay flash
        if self.flash_alpha > 0.0:
            self.flash_alpha = clamp(self.flash_alpha - self.flash_decay_per_ms * dt_ms, 0.0, 1.0)

        # subtle auto sway based on low frequency (bass) to give life
        self._bass_sway = math.sin(time.time() * 2.0) * (low * sensitivity * 6.0)

        # store last high for potential shimmer use (kept safe)
        self.last_high = high

    def paint(self, painter: QPainter, brightness: float):
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)

        # clamp brightness
        brightness = clamp(float(brightness), 0.1, 2.0)

        # compute eased progress
        t = ease_out_cubic(self.movement_progress)

        # pulse scale influenced by flash only (keeps discs at 20px base)
        pulse_scale = 1.0 + (self.flash_alpha * 0.15)
        # ensure diameter stays valid and positive
        radius_base = clamp(self.diameter * pulse_scale, 2.0, max(self.size.width(), self.size.height()))

        # Draw top row (only the 20px discs, no larger translucent halos)
        for i, orig_x in enumerate(self.orig_positions_top):
            # determine current x based on target state
            if self.move_to_center:
                cur_x = orig_x + (self.center_x - orig_x) * t
            else:
                # moving back to original: start from center
                cur_x = self.center_x + (orig_x - self.center_x) * t

            # apply subtle bass sway
            cur_x += math.sin((i + 1) * 0.3 + time.time() * 3.0) * (self._bass_sway * 0.02)

            # dynamic radius (keeps discs small and consistent)
            radius = radius_base
            radius = clamp(radius, 2.0, max(self.size.width(), self.size.height()))

            # color intensity modulated by flash and brightness
            v = clamp(self.base_val * (0.7 + 0.3 * (1.0 - self.flash_alpha)) * brightness, 0.0, 1.0)
            # add a small high-frequency shimmer by varying value slightly
            shimmer = 0.03 * math.sin(time.time() * 20.0 + i)
            v = clamp(v + shimmer, 0.0, 1.0)

            color = QColor.fromHsvF(self.hue, self.sat, v)
            brush = QBrush(color)
            painter.setBrush(brush)

            # draw disc centered at (cur_x, top_y)
            painter.drawEllipse(QPointF(cur_x - radius / 2.0, self.top_y - radius / 2.0),
                                radius / 2.0, radius / 2.0)

        # Draw bottom row (mirrored behavior) - only the 20px discs
        for i, orig_x in enumerate(self.orig_positions_bottom):
            if self.move_to_center:
                cur_x = orig_x + (self.center_x - orig_x) * t
            else:
                cur_x = self.center_x + (orig_x - self.center_x) * t

            cur_x += math.cos((i + 1) * 0.25 + time.time() * 2.5) * (self._bass_sway * 0.02)

            radius = radius_base
            radius = clamp(radius, 2.0, max(self.size.width(), self.size.height()))

            v = clamp(self.base_val * (0.7 + 0.3 * (1.0 - self.flash_alpha)) * brightness, 0.0, 1.0)
            shimmer = 0.03 * math.cos(time.time() * 18.0 + i)
            v = clamp(v + shimmer, 0.0, 1.0)

            color = QColor.fromHsvF(self.hue, self.sat, v)
            painter.setBrush(QBrush(color))
            painter.drawEllipse(QPointF(cur_x - radius / 2.0, self.bottom_y - radius / 2.0),
                                radius / 2.0, radius / 2.0)

        painter.restore()

    def on_beat(self):
        """
        Triggered by detected beats. Debounced to avoid rapid toggles.
        On each accepted beat we toggle the target state and start movement animation.
        """
        now_ms = time.time() * 1000.0
        if (now_ms - self.last_beat_time) < self.beat_debounce_ms:
            # ignore beat due to debounce
            return

        # accept beat
        self.last_beat_time = now_ms
        # toggle target
        self.move_to_center = not self.move_to_center
        # restart movement animation
        self.movement_progress = 0.0
        # call base implementation (keeps any internal bookkeeping)
        super().on_beat()
