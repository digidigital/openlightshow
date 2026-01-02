import math
import time
from PySide6.QtCore import QSize, QPointF, Qt
from PySide6.QtGui import QPainter, QColor, QPen, QPolygonF
from ..effect_base import Effect


class FrequencyMandala(Effect):
    """
    FrequencyMandala Effect:
    - Circular mandala pattern with rays growing from center to screen borders
    - Maximum 8 rays
    - Number of rays cycles based on beat count (3 to 8)
    - Ray length follows frequency bands and reaches screen borders:
      - Inner segment = bass (low)
      - Middle segment = mids
      - Outer segment = highs
    - Rotates slowly for hypnotic effect
    - 170ms beat debounce
    """

    name = "Frequency Mandala"
    effect_class = "centereffect_class01"

    def __init__(self, size: QSize):
        super().__init__(size)
        self.ray_count = 6
        self.rotation = 0.0
        self.beat_count = 0

        # Beat debounce
        self.last_beat_time = 0.0
        self.beat_debounce_ms = 200

        # Energy levels for three segments
        self.low_energy = 0.0
        self.mid_energy = 0.0
        self.high_energy = 0.0

    def on_beat(self):
        # Debounce: ignore beats too close together
        now = time.time() * 500.0
        if now - self.last_beat_time < self.beat_debounce_ms:
            return
        self.last_beat_time = now

        super().on_beat()

        # Increment beat count and cycle ray count (3 to 8 rays max)
        self.beat_count += 1
        self.ray_count = 3 + (self.beat_count % 6)  # 3, 4, 5, 6, 7, 8

    def update(self, dt_ms, energies, sensitivity, flash_thresh):
        # Store energy levels
        self.low_energy = energies.get('low', 0.0) * sensitivity
        self.mid_energy = energies.get('mid', 0.0) * sensitivity
        self.high_energy = energies.get('high', 0.0) * sensitivity

        # Slow rotation
        dt_sec = dt_ms / 1000.0
        self.rotation += dt_sec * 0.3  # 0.3 radians per second
        self.rotation %= (2 * math.pi)

    def paint(self, p: QPainter, brightness: float):
        p.save()
        p.setRenderHint(QPainter.Antialiasing, True)

        w, h = self.size.width(), self.size.height()
        cx, cy = w / 2, h / 2

        # Calculate max radius to reach screen borders in any direction
       
        max_radius = w/2 * 1.5

        # Three colors for three frequency bands
        color_low = QColor(255, 50, 50)    # Red for bass
        color_mid = QColor(50, 255, 50)    # Green for mids
        color_high = QColor(50, 150, 255)  # Blue for highs

        # Draw rays
        angle_step = (2 * math.pi) / self.ray_count

        for i in range(self.ray_count):
            angle = (i * angle_step) + self.rotation

            # Calculate direction
            dx = math.cos(angle)
            dy = math.sin(angle)

            # Three segments per ray - each reaches progressively further
            # Each segment's length is modulated by its corresponding frequency band

            # Inner segment (bass) - 0 to 33% of max_radius
            inner_len = max_radius * 0.33 * min(1.0, self.low_energy)
            if inner_len > 0:
                p1 = QPointF(cx, cy)
                p2 = QPointF(cx + dx * inner_len, cy + dy * inner_len)
                color = QColor(color_low)
                color.setAlphaF(max(0.0, min(1.0, brightness)))
                p.setPen(QPen(color, 4))
                p.drawLine(p1, p2)

            # Middle segment (mids) - 33% to 66% of max_radius
            mid_len = max_radius * 0.66 * min(1.0, self.mid_energy)
            if mid_len > 0:
                start_radius = max_radius * 0.33
                p1 = QPointF(cx + dx * start_radius, cy + dy * start_radius)
                p2 = QPointF(cx + dx * mid_len, cy + dy * mid_len)
                color = QColor(color_mid)
                color.setAlphaF(max(0.0, min(1.0, brightness)))
                p.setPen(QPen(color, 3))
                p.drawLine(p1, p2)

            # Outer segment (highs) - 66% to 100% of max_radius (reaches border)
            high_len = max_radius * min(1.0, self.high_energy)
            if high_len > 0:
                start_radius = max_radius * 0.66
                p1 = QPointF(cx + dx * start_radius, cy + dy * start_radius)
                p2 = QPointF(cx + dx * high_len, cy + dy * high_len)
                color = QColor(color_high)
                color.setAlphaF(max(0.0, min(1.0, brightness)))
                p.setPen(QPen(color, 2))
                p.drawLine(p1, p2)

        p.restore()
