import time
import random
import math
from PySide6.QtCore import QSize, QPointF, Qt
from PySide6.QtGui import QPainter, QColor, QPen, QPainterPath
from ..effect_base import Effect


class WavingLine(Effect):
    """
    WavingLine Effect:
    - Horizontal line anchored at screen center (h/2)
    - Waves smoothly like a sine/gaussian function between top and bottom
    - Bright colors that change on beat
    - Color shifts based on mid-range frequencies
    - Line thickness responds to bass energy
    - Wave amplitude modulated by music energy
    - Always bright (no fading)
    - 200ms beat debounce
    """

    name = "Waving Line"
    effect_class = "centereffect_class02"

    def __init__(self, size: QSize):
        super().__init__(size)

        # Beat debounce
        self.last_beat_time = 0.0
        self.beat_debounce_ms = 200

        # Oscillation parameters
        self.oscillation_phase = 0.0  # Current phase in oscillation cycle
        self.oscillation_speed = 0.25  # Oscillations per second (how fast it moves up/down)

        # Energy tracking
        self.bass_energy = 0.0
        self.mid_energy = 0.0
        self.high_energy = 0.0

        # Color shifting based on mids
        self.hue_shift = 0.0  # HSV hue value (0-360)

        # Neon colors - base colors to shift from
        self.neon_colors = [
            QColor(57, 255, 20),    # neon green
            QColor(255, 20, 147),   # neon pink
            QColor(0, 255, 255),    # neon cyan
            QColor(255, 255, 0),    # neon yellow
            QColor(255, 0, 255),    # neon magenta
            QColor(255, 165, 0),    # neon orange
            QColor(0, 255, 128),    # neon lime
            QColor(255, 50, 255),   # bright purple
        ]

        self.base_color = random.choice(self.neon_colors)

    def on_beat(self):
        # Debounce
        now = time.time()
        if (now - self.last_beat_time) * 1000.0 < self.beat_debounce_ms:
            return

        self.last_beat_time = now

        super().on_beat()

        # No color change on beat - keep constant color

    def update(self, dt_ms, energies, sensitivity, flash_thresh):
        # Track energies
        self.bass_energy = energies.get('low', 0.0) * sensitivity
        self.mid_energy = energies.get('mid', 0.0) * sensitivity
        self.high_energy = energies.get('high', 0.0) * sensitivity

        dt_sec = dt_ms / 1000.0

        # Update oscillation phase continuously
        self.oscillation_phase += self.oscillation_speed * dt_sec * 2 * math.pi
        self.oscillation_phase %= (2 * math.pi)

        # Update hue shift based on mid energy
        self.hue_shift += self.mid_energy * dt_sec * 360.0
        self.hue_shift %= 360.0

    def paint(self, p: QPainter, brightness: float):
        p.save()
        p.setRenderHint(QPainter.Antialiasing, True)

        w, h = self.size.width(), self.size.height()
        cy = h / 2.0  # Center y position (anchor point)

        # Line width based on bass energy
        line_width = 3.0 + self.bass_energy * 5.0

        # Color - apply hue shift based on mids
        base_hsv = self.base_color.toHsv()
        h, s, v, a = base_hsv.getHsv()

        # Shift hue
        new_hue = (h + self.hue_shift) % 360
        color = QColor.fromHsv(int(new_hue), s, v, a)
        color.setAlphaF(max(0.0, min(1.0, brightness)))

        pen = QPen(color, line_width)
        p.setPen(pen)

        # Create waving line path - symmetric parabolic curve
        path = QPainterPath()

        # Number of segments for smooth curve
        num_segments = 200
        segment_width = w / num_segments

        # Calculate oscillation offset (moves between -1 and +1)
        # sin(phase) oscillates smoothly: 0 → 1 → 0 → -1 → 0
        oscillation_factor = math.sin(self.oscillation_phase)

        # Safety margin to keep line on screen
        safety_margin = 10.0

        # Calculate where the peak of the parabola should be
        # When oscillation_factor = 1: peak at safety_margin (near top)
        # When oscillation_factor = -1: peak at h - safety_margin (near bottom)
        # When oscillation_factor = 0: peak at h/2 (center)
        peak_y = cy - oscillation_factor * (cy - safety_margin)

        # Start path
        first_point = True

        for i in range(num_segments + 1):
            x = i * segment_width

            # Normalized position from -1 (left edge) to +1 (right edge)
            # Center (w/2) maps to 0
            normalized_x = (x - w/2) / (w/2)

            # Parabolic curve: 1 at center (x=0), falls to 0 at edges
            curve_shape = 1.0 - normalized_x * normalized_x

            # The curve extends from peak_y (at center) toward cy (at edges)
            # At center: y = peak_y
            # At edges: y = cy
            y = peak_y + (cy - peak_y) * (1.0 - curve_shape)

            if first_point:
                path.moveTo(x, y)
                first_point = False
            else:
                path.lineTo(x, y)

        # Draw the path
        p.drawPath(path)

        p.restore()
