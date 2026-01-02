import time
import random
import math
from PySide6.QtCore import QSize, QPointF, Qt
from PySide6.QtGui import QPainter, QColor, QPen
from ..effect_base import Effect


class OrbitingSatellites(Effect):
    """
    Orbiting Satellites Effect:
    - Small circles orbiting around the center at different radii and speeds
    - Bass controls number of visible satellites (1-8)
    - Mids control orbital speed multiplier
    - Highs control trail length (motion blur)
    - Beat reverses orbit direction
    - 200ms beat debounce
    """

    name = "Orbiting Satellites"
    effect_class = "orbiteffect_class01"

    def __init__(self, size: QSize):
        super().__init__(size)

        # Beat debounce
        self.last_beat_time = 0.0
        self.beat_debounce_ms = 200

        # Satellites - more dots
        self.max_satellites = 16
        self.satellites = []
        self._init_satellites()

        # Orbit direction (1 = counter-clockwise, -1 = clockwise)
        self.direction = 1

        # Beat counter for less frequent direction changes
        self.beat_count = 0

        # Visibility/fade tracking
        self.visibility = 1.0  # 0.0 to 1.0

        # Energy tracking
        self.bass_energy = 0.0
        self.mid_energy = 0.0
        self.high_energy = 0.0

    def _init_satellites(self):
        """Initialize satellites at different orbital radii and speeds"""
        self.satellites = []
        for i in range(self.max_satellites):
            # Each satellite has a different orbital radius - fill more screen
            radius_factor = 0.15 + (i / self.max_satellites) * 0.75  # 0.15 to 0.9
            base_speed = 3.0 + random.uniform(-0.8, 0.8)  # Even faster: 2.2-3.8 rad/s

            self.satellites.append({
                "angle": random.uniform(0, 2 * math.pi),  # Starting angle
                "radius_factor": radius_factor,
                "base_speed": base_speed,
                "color": QColor(
                    random.randint(100, 255),
                    random.randint(100, 255),
                    random.randint(100, 255)
                ),
                "size": random.uniform(3.0, 6.0)
            })

        # Initialize trails - always create list with max_satellites entries
        self.trails = [[] for _ in range(self.max_satellites)]

    def on_beat(self):
        # Debounce
        now = time.time()
        if (now - self.last_beat_time) * 1000.0 < self.beat_debounce_ms:
            return

        self.last_beat_time = now

        super().on_beat()

        # Beat makes effect visible
        self.visibility = 1.0

        # Reverse orbit direction every 4 beats (less jarring)
        self.beat_count += 1
        if self.beat_count >= 4:
            self.direction *= -1
            self.beat_count = 0

    def update(self, dt_ms, energies, sensitivity, flash_thresh):
        # Track energies
        self.bass_energy = energies.get('low', 0.0) * sensitivity
        self.mid_energy = energies.get('mid', 0.0) * sensitivity
        self.high_energy = energies.get('high', 0.0) * sensitivity

        dt_sec = dt_ms / 1000.0

        # Fade out slowly when no bass (slower fade)
        if self.bass_energy < 0.1:
            # Very slow fade out
            self.visibility -= dt_sec * 0.15  # Takes ~6.7 seconds to fully fade
        else:
            # Fade in on bass (keep visible)
            self.visibility = min(1.0, self.visibility + dt_sec * 2.0)

        self.visibility = max(0.0, min(1.0, self.visibility))

        # Ensure trails list is properly sized
        if len(self.trails) != self.max_satellites:
            self.trails = [[] for _ in range(self.max_satellites)]

        # Constant speed - no music modulation for stable rotation
        speed_mult = 1.0

        # Update satellite positions
        for i, sat in enumerate(self.satellites):
            # Update angle based on speed, direction, and mid energy
            angle_delta = sat["base_speed"] * speed_mult * self.direction * dt_sec
            sat["angle"] += angle_delta
            sat["angle"] %= (2 * math.pi)

            # Update trail based on high energy
            max_trail_length = int(self.high_energy * 30)  # 0-30 trail points

            if max_trail_length > 0:
                # Get current position for trail
                w, h = self.size.width(), self.size.height()
                cx, cy = w / 2.0, h / 2.0
                max_radius = min(w, h) * 0.45
                radius = max_radius * sat["radius_factor"]

                x = cx + radius * math.cos(sat["angle"])
                y = cy + radius * math.sin(sat["angle"])

                # Add to trail
                self.trails[i].append(QPointF(x, y))

                # Limit trail length
                if len(self.trails[i]) > max_trail_length:
                    self.trails[i].pop(0)
            else:
                # Clear trail if highs are low
                self.trails[i].clear()

    def paint(self, p: QPainter, brightness: float):
        p.save()
        p.setRenderHint(QPainter.Antialiasing, True)

        w, h = self.size.width(), self.size.height()
        cx, cy = w / 2.0, h / 2.0

        # Maximum orbital radius
        max_radius = min(w, h) * 0.45

        # Show all satellites
        num_visible = self.max_satellites

        # Draw trails first (so satellites are on top)
        for i in range(num_visible):
            sat = self.satellites[i]
            trail = self.trails[i]

            if len(trail) > 1:
                color = QColor(sat["color"])

                # Draw trail with fading alpha, modulated by visibility
                for j in range(len(trail) - 1):
                    # Alpha fades from 0 (oldest) to current brightness (newest)
                    trail_alpha = brightness * self.visibility * (j / len(trail)) * 0.5
                    color.setAlphaF(max(0.0, min(1.0, trail_alpha)))

                    pen = QPen(color, 1.5)
                    p.setPen(pen)
                    p.drawLine(trail[j], trail[j + 1])

        # Draw satellites
        for i in range(num_visible):
            sat = self.satellites[i]

            # Calculate position
            radius = max_radius * sat["radius_factor"]
            x = cx + radius * math.cos(sat["angle"])
            y = cy + radius * math.sin(sat["angle"])

            # Color with brightness and visibility
            color = QColor(sat["color"])
            color.setAlphaF(max(0.0, min(1.0, brightness * self.visibility)))

            p.setPen(Qt.NoPen)
            p.setBrush(color)
            p.drawEllipse(QPointF(x, y), sat["size"], sat["size"])

        p.restore()
