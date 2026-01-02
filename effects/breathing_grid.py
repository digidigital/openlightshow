import time
import math
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QPainter, QColor, QPen
from ..effect_base import Effect


class BreathingGrid(Effect):
    """
    Breathing Grid Effect:
    - Grid of lines that expands and contracts like breathing
    - Bass controls expansion/contraction intensity
    - Mids shift color through HSV spectrum
    - Highs control grid density
    - Beat inverts grid orientation
    - 200ms beat debounce
    """

    name = "Breathing Grid"
    effect_class = "grideffect_class01"

    def __init__(self, size: QSize):
        super().__init__(size)

        # Beat debounce
        self.last_beat_time = 0.0
        self.beat_debounce_ms = 200

        # Breathing animation
        self.phase = 0.0
        self.base_speed = 0.0005  # Base breathing speed

        # Grid state
        self.horizontal = True  # True = horizontal lines, False = vertical lines

        # Energy tracking
        self.bass_energy = 0.0
        self.mid_energy = 0.0
        self.high_energy = 0.0

        # Color
        self.hue = 0.0

    def on_beat(self):
        # Debounce
        now = time.time()
        if (now - self.last_beat_time) * 1000.0 < self.beat_debounce_ms:
            return

        self.last_beat_time = now

        super().on_beat()

        # Invert grid orientation on beat
        self.horizontal = not self.horizontal

    def update(self, dt_ms, energies, sensitivity, flash_thresh):
        # Track energies
        self.bass_energy = energies.get('low', 0.0) * sensitivity
        self.mid_energy = energies.get('mid', 0.0) * sensitivity
        self.high_energy = energies.get('high', 0.0) * sensitivity

        dt_sec = dt_ms / 1000.0

        # Update breathing phase
        speed = self.base_speed * (1.0 + self.bass_energy)
        self.phase += dt_sec * speed
        self.phase %= (2 * math.pi)

        # Update hue shift based on mid energy
        self.hue += self.mid_energy * dt_sec * 180.0
        self.hue %= 360.0

    def paint(self, p: QPainter, brightness: float):
        p.save()
        p.setRenderHint(QPainter.Antialiasing, True)

        w, h = self.size.width(), self.size.height()
        cx, cy = w / 2.0, h / 2.0

        # Breathing effect: oscillate between 0.6 and 1.0
        breath = 0.8 + 0.2 * math.sin(self.phase)

        # Bass intensifies the breathing range
        breath_intensity = breath + self.bass_energy * 0.3

        # Grid density based on highs (1-5 lines) - 1/4 of original
        base_lines = 2.5
        line_count = int(base_lines + self.high_energy * 2.5)
        line_count = max(1, min(line_count, 5))

        # Color with hue shift
        hue_val = int(self.hue) % 360
        color = QColor.fromHsv(hue_val, 200, 255)
        color.setAlphaF(max(0.0, min(1.0, brightness)))

        pen = QPen(color, 2)
        p.setPen(pen)

        if self.horizontal:
            # Horizontal lines
            spacing = h / float(line_count)
            for i in range(line_count + 1):
                y_base = i * spacing
                # Calculate offset from center
                offset_from_center = abs(y_base - cy)
                # Apply breathing effect - lines near center move more
                breathing_offset = (cy - offset_from_center) / cy * (breath_intensity - 0.8) * cy * 0.3
                y = y_base + breathing_offset if y_base < cy else y_base - breathing_offset
                p.drawLine(0, int(y), w, int(y))
        else:
            # Vertical lines
            spacing = w / float(line_count)
            for i in range(line_count + 1):
                x_base = i * spacing
                # Calculate offset from center
                offset_from_center = abs(x_base - cx)
                # Apply breathing effect - lines near center move more
                breathing_offset = (cx - offset_from_center) / cx * (breath_intensity - 0.8) * cx * 0.3
                x = x_base + breathing_offset if x_base < cx else x_base - breathing_offset
                p.drawLine(int(x), 0, int(x), h)

        p.restore()
