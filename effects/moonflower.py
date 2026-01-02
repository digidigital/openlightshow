"""
Moonflower effect - Rotating light spots in a flower pattern.

Behavior:
- Multiple light spots rotate around the canvas in a circular pattern
- Spots expand/contract (bloom) like a flower opening and closing
- Creates classic moonflower lighting effect
- Bass: Controls bloom intensity (how wide the pattern spreads)
- Mids: Modulates rotation speed
- Highs: Controls number of spots (4-12)
- Beat: Triggers bloom pulse and color change
"""

import math
import time
from PySide6.QtCore import QPointF, QSize
from PySide6.QtGui import QPainter, QColor, QPen, QRadialGradient
from ..effect_base import Effect


class MoonflowerEffect(Effect):
    name = "Moonflower"
    effect_class = "moonflowereffect_class01"

    def __init__(self, size: QSize):
        super().__init__(size)
        self.rotation_angle = 0.0
        self.bloom_phase = 0.0  # Controls how open the flower is
        self.num_spots = 16  # Fixed number of spots
        self.hue = 0.0

        # Music reactive values
        self.bass_energy = 0.0
        self.mid_energy = 0.0
        self.high_energy = 0.0

        # Beat detection
        self.last_beat_time = 0.0
        self.beat_pulse = 0.0  # Decays after beat

        # Base parameters
        self.base_rotation_speed = 60.0  # Degrees per second (doubled)
        self.screen_margin = 40  # Pixels margin from screen edge

    def on_beat(self):
        """Triggered on beat detection."""
        current_time = time.time() * 1000.0

        # Debounce beats (200ms)
        if current_time - self.last_beat_time < 200:
            return

        self.last_beat_time = current_time

        # Trigger bloom pulse
        self.beat_pulse = 1.0

        # Change hue on beat
        self.hue = (self.hue + 0.15) % 1.0

    def update(self, dt_ms, energies, sensitivity, flash_thresh):
        """Update effect state."""
        dt_sec = dt_ms / 1000.0

        # Extract energy values
        self.bass_energy = energies.get('low', 0.0) * sensitivity
        self.mid_energy = energies.get('mid', 0.0) * sensitivity
        self.high_energy = energies.get('high', 0.0) * sensitivity

        # Update rotation - mids modulate speed
        speed_multiplier = 1.0 + self.mid_energy * 2.0
        rotation_speed = self.base_rotation_speed * speed_multiplier
        self.rotation_angle += rotation_speed * dt_sec
        self.rotation_angle = self.rotation_angle % 360.0

        # Update bloom phase - oscillates naturally
        bloom_speed = 0.8  # Cycles per second
        self.bloom_phase += bloom_speed * dt_sec

        # Decay beat pulse
        if self.beat_pulse > 0:
            self.beat_pulse -= dt_sec * 3.0
            self.beat_pulse = max(0.0, self.beat_pulse)

        # Slow hue drift when no beats
        if self.beat_pulse <= 0:
            self.hue += dt_sec * 0.05
            self.hue = self.hue % 1.0

    def paint(self, p: QPainter, brightness: float):
        """Render the moonflower effect."""
        p.save()

        w, h = self.size.width(), self.size.height()
        cx, cy = w / 2.0, h / 2.0

        # Calculate bloom factor (how open the flower is)
        natural_bloom = 0.5 + 0.5 * math.sin(self.bloom_phase)
        bass_bloom = self.bass_energy * 0.3
        pulse_bloom = self.beat_pulse * 0.2
        bloom_factor = natural_bloom + bass_bloom + pulse_bloom
        bloom_factor = max(0.0, min(1.0, bloom_factor))

        # Calculate maximum radius to reach screen edges with margin
        # Use vertical distance (half height minus margin) as it's typically smaller
        max_radius_vertical = (h / 2.0) - self.screen_margin
        max_radius_horizontal = (w / 2.0) - self.screen_margin
        max_radius = min(max_radius_vertical, max_radius_horizontal)

        # Radius oscillates from 0 to max_radius based on bloom
        radius = max_radius * bloom_factor

        # Draw each spot
        angle_step = 360.0 / self.num_spots

        for i in range(self.num_spots):
            # Calculate spot position
            spot_angle = self.rotation_angle + (i * angle_step)
            spot_angle_rad = math.radians(spot_angle)

            spot_x = cx + radius * math.cos(spot_angle_rad)
            spot_y = cy + radius * math.sin(spot_angle_rad)

            # Alternate colors for adjacent spots
            color_offset = (i % 2) * 0.5
            spot_hue = (self.hue + color_offset) % 1.0

            # Draw spot
            self._draw_spot(p, spot_x, spot_y, spot_hue, bloom_factor, brightness)

        p.restore()

    def _draw_spot(self, p: QPainter, x, y, hue, bloom, brightness_val):
        """Draw a single light spot."""
        # Spot size varies with bloom
        spot_size = 20 + bloom * 30

        # Create radial gradient
        gradient = QRadialGradient(x, y, spot_size)

        # Color intensity varies with bloom (clamped to valid range)
        intensity = min(1.0, 0.8 + bloom * 0.2 + self.beat_pulse * 0.3)

        # Bright center
        center_color = QColor.fromHsvF(hue, 0.8, intensity)
        center_alpha = max(0.0, min(1.0, brightness_val * 0.9))
        center_color.setAlphaF(center_alpha)

        # Fade to edges
        edge_color = QColor.fromHsvF(hue, 0.9, 0.6)
        edge_alpha = max(0.0, min(1.0, brightness_val * 0.2))
        edge_color.setAlphaF(edge_alpha)

        gradient.setColorAt(0.0, center_color)
        gradient.setColorAt(0.6, edge_color)
        gradient.setColorAt(1.0, QColor(0, 0, 0, 0))

        p.setPen(QPen(QColor(0, 0, 0, 0)))
        p.setBrush(gradient)
        p.drawEllipse(QPointF(x, y), spot_size, spot_size)

        # Draw brighter core
        core_size = spot_size * 0.4
        core_color = QColor.fromHsvF(hue, 0.5, 1.0)
        core_alpha = max(0.0, min(1.0, brightness_val * 0.8))
        core_color.setAlphaF(core_alpha)
        p.setBrush(core_color)
        p.drawEllipse(QPointF(x, y), core_size, core_size)
