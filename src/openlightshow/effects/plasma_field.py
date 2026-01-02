import time
import random
import math
from PySide6.QtCore import QSize, QPointF, Qt
from PySide6.QtGui import QPainter, QColor, QPen
from ..effect_base import Effect


class PlasmaField(Effect):
    """
    Plasma Field Effect:
    - Field of dots that pulse and change color based on distance from hot spot
    - Bass controls pulse intensity
    - Mids move the hot spot center point
    - Highs control color temperature (blue to red)
    - Beat resets dots to new random positions
    - 200ms beat debounce
    """

    name = "Plasma Field"
    effect_class = "particle_class01"

    def __init__(self, size: QSize):
        super().__init__(size)

        # Beat debounce
        self.last_beat_time = 0.0
        self.beat_debounce_ms = 200

        # Dots
        self.dots = []
        self.num_dots = 150
        self._init_dots()

        # Hot spot (energy center)
        self.hot_spot_x = 0.5  # Normalized position (0-1)
        self.hot_spot_y = 0.5
        self.hot_spot_phase = 0.0  # For oscillation

        # Energy tracking
        self.bass_energy = 0.0
        self.mid_energy = 0.0
        self.high_energy = 0.0

    def _init_dots(self):
        """Initialize dots at random positions"""
        self.dots = []
        for _ in range(self.num_dots):
            self.dots.append({
                "x": random.random(),  # Normalized 0-1
                "y": random.random(),
                "base_size": random.uniform(2.0, 5.0)
            })

    def on_beat(self):
        # Debounce
        now = time.time()
        if (now - self.last_beat_time) * 1000.0 < self.beat_debounce_ms:
            return

        self.last_beat_time = now

        super().on_beat()

        # Reset dots to new positions
        self._init_dots()

    def update(self, dt_ms, energies, sensitivity, flash_thresh):
        # Track energies
        self.bass_energy = energies.get('low', 0.0) * sensitivity
        self.mid_energy = energies.get('mid', 0.0) * sensitivity
        self.high_energy = energies.get('high', 0.0) * sensitivity

        dt_sec = dt_ms / 1000.0

        # Move hot spot in a figure-8 pattern, modulated by mids
        self.hot_spot_phase += dt_sec * (0.5 + self.mid_energy)

        # Figure-8 (Lissajous curve)
        self.hot_spot_x = 0.5 + 0.3 * math.sin(self.hot_spot_phase)
        self.hot_spot_y = 0.5 + 0.3 * math.sin(2 * self.hot_spot_phase)

    def paint(self, p: QPainter, brightness: float):
        p.save()
        p.setRenderHint(QPainter.Antialiasing, True)

        w, h = self.size.width(), self.size.height()

        # Hot spot position in screen coordinates
        hot_x = self.hot_spot_x * w
        hot_y = self.hot_spot_y * h

        # Maximum distance for normalization
        max_dist = math.sqrt(w * w + h * h) / 2.0

        for dot in self.dots:
            # Dot position in screen coordinates
            dx = dot["x"] * w
            dy = dot["y"] * h

            # Distance from hot spot
            dist = math.sqrt((dx - hot_x) ** 2 + (dy - hot_y) ** 2)

            # Normalize distance (0 = at hot spot, 1 = far away)
            norm_dist = min(1.0, dist / max_dist)

            # Pulse effect based on bass (closer dots pulse more)
            pulse = 1.0 + self.bass_energy * (1.0 - norm_dist) * 0.5

            # Size based on distance and pulse
            size = dot["base_size"] * pulse

            # Color temperature based on distance and high energy
            # Close to hot spot: red/orange, Far away: blue
            # High energy shifts everything toward red
            temp_shift = self.high_energy * 0.5

            if norm_dist < 0.5:
                # Close to hot spot - red/orange/yellow
                hue = int(0 + temp_shift * 60)  # 0-60 (red to yellow)
            else:
                # Far from hot spot - cyan/blue
                hue = int(200 - temp_shift * 100)  # 200-100 (cyan to green)

            hue = hue % 360
            sat = 255
            val = int(200 + (1.0 - norm_dist) * 55)  # Brighter near hot spot

            color = QColor.fromHsv(hue, sat, val)

            # Alpha based on distance (closer = more opaque)
            alpha = brightness * (1.2 - norm_dist * 0.5)
            color.setAlphaF(max(0.0, min(1.0, alpha)))

            p.setPen(Qt.NoPen)
            p.setBrush(color)
            p.drawEllipse(QPointF(dx, dy), size, size)

        p.restore()
