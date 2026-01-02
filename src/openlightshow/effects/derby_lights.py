"""
DerbyLights effect - Rotating multi-colored light spots (projection only).

Behavior:
- Multiple sets of rotating colored spots fill the canvas
- Each set has exactly 5 spots in different colors rotating around a center point
- Spots rotate continuously in opposite directions (CW and CCW)
- Creates chaotic, overlapping colored light patterns
- Bass: Rotation speed boost and color changes
- Highs: Spot intensity and flash effects
- Beat: Direction reversal and color shifts
"""

import math
import time
import random
from PySide6.QtCore import QPointF, QSize
from PySide6.QtGui import QPainter, QColor, QPen, QRadialGradient
from ..effect_base import Effect


class DerbySpotSet:
    """Represents a set of rotating colored spots."""
    def __init__(self, center_x, center_y, index):
        self.center_x = center_x
        self.center_y = center_y
        self.num_spots = 5  # Fixed at 5 spots
        self.rotation = random.uniform(0, 360)
        self.rotation_direction = 1 if index % 2 == 0 else -1  # Alternate CW/CCW

        # Spot colors - classic derby uses 5 colors (Red, Green, Blue, Yellow, Magenta)
        self.spot_colors = [
            0.0,    # Red
            0.33,   # Green
            0.66,   # Blue
            0.16,   # Yellow
            0.83,   # Magenta
        ]

        # Spot characteristics
        self.orbit_radius = 0.15  # Relative to screen size


class DerbyLightsEffect(Effect):
    name = "DerbyLights"
    effect_class = "centereffect_class03"

    def __init__(self, size: QSize):
        super().__init__(size)
        self.spot_sets = []
        self.num_sets = 3  # Minimum 3 instances
        self._initialize_spot_sets()

        # Music reactive values
        self.bass_energy = 0.0
        self.mid_energy = 0.0
        self.high_energy = 0.0

        # Beat detection
        self.last_beat_time = 0.0
        self.beat_pulse = 0.0
        self.beat_count = 0

        # Global effects
        self.color_shift = 0.0
        self.flash_on = True

        # Base rotation speed
        self.base_rotation_speed = 300.0  # Degrees per second (5x faster)

    def resize(self, size: QSize):
        """Handle window resize."""
        super().resize(size)
        self._initialize_spot_sets()

    def _initialize_spot_sets(self):
        """Create spot sets evenly distributed across the screen."""
        w, h = self.size.width(), self.size.height()
        self.spot_sets = []

        # Create evenly distributed grid positions based on num_sets
        # For 3 sets: triangle pattern (top-left, top-right, bottom-center)
        # For 4 sets: corners (TL, TR, BL, BR)
        # For 5+ sets: evenly spaced grid

        if self.num_sets == 3:
            positions = [
                (w * 0.25, h * 0.33),  # Upper left
                (w * 0.75, h * 0.33),  # Upper right
                (w * 0.5, h * 0.67),   # Bottom center
            ]
        elif self.num_sets == 4:
            positions = [
                (w * 0.25, h * 0.25),  # Upper left
                (w * 0.75, h * 0.25),  # Upper right
                (w * 0.25, h * 0.75),  # Lower left
                (w * 0.75, h * 0.75),  # Lower right
            ]
        elif self.num_sets == 5:
            positions = [
                (w * 0.5, h * 0.2),    # Top center
                (w * 0.2, h * 0.5),    # Middle left
                (w * 0.5, h * 0.5),    # Center
                (w * 0.8, h * 0.5),    # Middle right
                (w * 0.5, h * 0.8),    # Bottom center
            ]
        elif self.num_sets == 6:
            positions = [
                (w * 0.25, h * 0.25),  # Upper left
                (w * 0.5, h * 0.25),   # Upper center
                (w * 0.75, h * 0.25),  # Upper right
                (w * 0.25, h * 0.75),  # Lower left
                (w * 0.5, h * 0.75),   # Lower center
                (w * 0.75, h * 0.75),  # Lower right
            ]
        else:
            # For other numbers, create a grid pattern
            cols = int(math.ceil(math.sqrt(self.num_sets)))
            rows = int(math.ceil(self.num_sets / cols))
            positions = []
            for i in range(self.num_sets):
                row = i // cols
                col = i % cols
                x = (col + 1) * w / (cols + 1)
                y = (row + 1) * h / (rows + 1)
                positions.append((x, y))

        for i in range(self.num_sets):
            pos = positions[i]
            spot_set = DerbySpotSet(pos[0], pos[1], i)
            self.spot_sets.append(spot_set)

    def on_beat(self):
        """Triggered on beat detection."""
        current_time = time.time() * 1000.0

        # Debounce beats (200ms)
        if current_time - self.last_beat_time < 200:
            return

        self.last_beat_time = current_time
        self.beat_count += 1
        self.beat_pulse = 1.0

        # Reverse rotation direction on beat
        for spot_set in self.spot_sets:
            spot_set.rotation_direction *= -1

        # Shift colors
        self.color_shift = (self.color_shift + random.uniform(0.1, 0.3)) % 1.0

        # Every 8 beats, change number of spot sets (3-6 sets)
        if self.beat_count % 8 == 0:
            self.num_sets = random.randint(3, 6)
            self._initialize_spot_sets()

    def update(self, dt_ms, energies, sensitivity, flash_thresh):
        """Update effect state."""
        dt_sec = dt_ms / 1000.0

        # Extract energy values
        self.bass_energy = energies.get('low', 0.0) * sensitivity
        self.mid_energy = energies.get('mid', 0.0) * sensitivity
        self.high_energy = energies.get('high', 0.0) * sensitivity

        # Calculate rotation speed - bass boosts speed
        rotation_speed = self.base_rotation_speed * (1.0 + self.bass_energy * 2.0)

        # Update each spot set
        for spot_set in self.spot_sets:
            # Rotate spots
            spot_set.rotation += rotation_speed * spot_set.rotation_direction * dt_sec
            spot_set.rotation = spot_set.rotation % 360.0

        # Flash effect based on high energy
        if self.high_energy > 0.8:
            # Strobe at high frequency
            self.flash_on = int(time.time() * 20) % 2 == 0
        else:
            self.flash_on = True

        # Decay beat pulse
        if self.beat_pulse > 0:
            self.beat_pulse -= dt_sec * 3.0
            self.beat_pulse = max(0.0, self.beat_pulse)

        # Slow color drift
        self.color_shift += dt_sec * 0.05
        self.color_shift = self.color_shift % 1.0

    def paint(self, p: QPainter, brightness: float):
        """Render the derby lights spots."""
        p.save()

        if not self.flash_on:
            p.restore()
            return

        w, h = self.size.width(), self.size.height()
        orbit_radius = min(w, h) * 0.15

        # Draw all spot sets
        for spot_set in self.spot_sets:
            self._draw_spot_set(p, spot_set, orbit_radius, brightness)

        p.restore()

    def _draw_spot_set(self, p: QPainter, spot_set, orbit_radius, brightness_val):
        """Draw a set of rotating spots."""
        angle_step = 360.0 / spot_set.num_spots

        for i in range(spot_set.num_spots):
            spot_angle = spot_set.rotation + (i * angle_step)
            spot_hue = (spot_set.spot_colors[i] + self.color_shift) % 1.0

            # Calculate spot position
            spot_angle_rad = math.radians(spot_angle)
            spot_x = spot_set.center_x + orbit_radius * math.cos(spot_angle_rad)
            spot_y = spot_set.center_y + orbit_radius * math.sin(spot_angle_rad)

            # Draw spot
            self._draw_spot(p, spot_x, spot_y, spot_hue, brightness_val)

    def _draw_spot(self, p: QPainter, x, y, hue, brightness_val):
        """Draw a single colored spot."""
        # Spot size with beat pulse
        spot_size = 25 + self.beat_pulse * 15

        # Create radial gradient
        gradient = QRadialGradient(x, y, spot_size)

        # Intensity with high energy and beat pulse (clamped to valid range)
        intensity = min(1.0, 0.8 + self.high_energy * 0.2 + self.beat_pulse * 0.3)

        # Bright center
        center_color = QColor.fromHsvF(hue, 0.9, intensity)
        center_alpha = max(0.0, min(1.0, brightness_val * 0.9))
        center_color.setAlphaF(center_alpha)

        # Fade at edges
        edge_color = QColor.fromHsvF(hue, 0.7, 0.6)
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
