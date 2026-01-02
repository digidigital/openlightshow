"""
Butterfly effect - Dual symmetric light spots that sweep like butterfly wings.

Behavior:
- Four light spots (two wing pairs) that sweep open and close
- Spots move in symmetric butterfly wing motion
- Can operate in different modes: horizontal, vertical, or rotating
- Bass: Controls sweep speed and intensity
- Mids: Controls spot size
- Highs: Modulates brightness pulses
- Beat: Triggers wing flap (quick close/open) and mode change
"""

import math
import time
from PySide6.QtCore import QPointF, QSize
from PySide6.QtGui import QPainter, QColor, QPen, QRadialGradient
from ..effect_base import Effect


class ButterflyEffect(Effect):
    name = "Butterfly"
    effect_class = "butterflyeffect_class01"

    def __init__(self, size: QSize):
        super().__init__(size)
        self.wing_angle = 0.0  # Current angle of wings from center
        self.sweep_phase = 0.0  # Phase of the sweep oscillation
        self.rotation_angle = 0.0  # Overall rotation of the butterfly
        self.hue = 0.33  # Start with green/cyan

        # Music reactive values
        self.bass_energy = 0.0
        self.mid_energy = 0.0
        self.high_energy = 0.0

        # Beat detection
        self.last_beat_time = 0.0
        self.beat_pulse = 0.0
        self.flap_trigger = 0.0  # Quick wing flap on beat

        # Mode (0=horizontal, 1=vertical, 2=rotating)
        self.mode = 0
        self.beat_count = 0

        # Base parameters
        self.min_wing_angle = 10.0  # Minimum angle between wings (degrees)
        self.max_wing_angle = 160.0  # Maximum angle between wings (degrees)
        self.base_sweep_speed = 1.2  # Oscillations per second
        self.rotation_speed = 15.0  # Degrees per second for rotating mode

    def on_beat(self):
        """Triggered on beat detection."""
        current_time = time.time() * 1000.0

        # Debounce beats (200ms)
        if current_time - self.last_beat_time < 200:
            return

        self.last_beat_time = current_time
        self.beat_count += 1

        # Trigger wing flap
        self.flap_trigger = 1.0

        # Pulse effect
        self.beat_pulse = 1.0

        # Change mode every 8 beats
        if self.beat_count % 8 == 0:
            self.mode = (self.mode + 1) % 3

        # Shift hue on beat
        self.hue = (self.hue + 0.12) % 1.0

    def update(self, dt_ms, energies, sensitivity, flash_thresh):
        """Update effect state."""
        dt_sec = dt_ms / 1000.0

        # Extract energy values
        self.bass_energy = energies.get('low', 0.0) * sensitivity
        self.mid_energy = energies.get('mid', 0.0) * sensitivity
        self.high_energy = energies.get('high', 0.0) * sensitivity

        # Update sweep phase - bass controls speed
        sweep_speed = self.base_sweep_speed * (1.0 + self.bass_energy * 1.5)
        self.sweep_phase += sweep_speed * dt_sec

        # Calculate wing angle with smooth oscillation
        base_oscillation = math.sin(self.sweep_phase * math.pi)

        # Add flap effect (quick close on beat)
        flap_factor = 1.0 - (self.flap_trigger * 0.7)

        # Map oscillation to wing angle range
        angle_range = self.max_wing_angle - self.min_wing_angle
        self.wing_angle = self.min_wing_angle + (angle_range * (base_oscillation + 1.0) / 2.0) * flap_factor

        # Update rotation for rotating mode
        if self.mode == 2:
            # Rotating mode - continuous rotation
            self.rotation_angle += self.rotation_speed * dt_sec
            self.rotation_angle = self.rotation_angle % 360.0
        else:
            # Fixed orientation modes - smoothly transition to target angle
            if self.mode == 0:  # Horizontal
                target_angle = 0.0
            else:  # Vertical
                target_angle = 90.0

            # Smoothly interpolate to target angle
            angle_diff = target_angle - self.rotation_angle
            # Handle wrap-around (choose shortest path)
            if angle_diff > 180.0:
                angle_diff -= 360.0
            elif angle_diff < -180.0:
                angle_diff += 360.0

            # Smooth transition (10% per frame)
            self.rotation_angle += angle_diff * min(1.0, dt_sec * 5.0)
            self.rotation_angle = self.rotation_angle % 360.0

        # Decay beat effects
        if self.beat_pulse > 0:
            self.beat_pulse -= dt_sec * 4.0
            self.beat_pulse = max(0.0, self.beat_pulse)

        if self.flap_trigger > 0:
            self.flap_trigger -= dt_sec * 5.0
            self.flap_trigger = max(0.0, self.flap_trigger)

        # Slow hue drift
        self.hue += dt_sec * 0.03
        self.hue = self.hue % 1.0

    def paint(self, p: QPainter, brightness: float):
        """Render the butterfly effect."""
        p.save()

        w, h = self.size.width(), self.size.height()
        cx, cy = w / 2.0, h / 2.0
        max_distance = min(w, h) * 0.4

        # Spot size based on mid energy
        base_spot_size = 25
        spot_size = base_spot_size + self.mid_energy * 30

        # Calculate the four wing spot angles
        half_angle = self.wing_angle / 2.0

        # Apply rotation based on mode
        base_angle = self.rotation_angle

        wing1_angle = base_angle + half_angle
        wing2_angle = base_angle - half_angle
        wing3_angle = base_angle + 180.0 + half_angle
        wing4_angle = base_angle + 180.0 - half_angle

        # Colors - create complementary colors for each wing pair
        color1_hue = self.hue
        color2_hue = (self.hue + 0.5) % 1.0  # Complementary color

        # Brightness modulation from high energy
        brightness_mod = 1.0 + self.high_energy * 0.3 + self.beat_pulse * 0.4

        # Draw the four wing spots
        wings = [
            (wing1_angle, color1_hue),
            (wing2_angle, color1_hue),
            (wing3_angle, color2_hue),
            (wing4_angle, color2_hue),
        ]

        for angle_deg, hue in wings:
            angle_rad = math.radians(angle_deg)

            # Calculate spot position
            spot_x = cx + max_distance * math.cos(angle_rad)
            spot_y = cy + max_distance * math.sin(angle_rad)

            # Draw spot
            self._draw_spot(p, spot_x, spot_y, spot_size, hue, brightness * brightness_mod)

        p.restore()

    def _draw_spot(self, p: QPainter, x, y, size, hue, brightness_val):
        """Draw a single light spot."""
        # Create radial gradient for glow
        gradient = QRadialGradient(x, y, size)

        # Bright center
        center_color = QColor.fromHsvF(hue, 0.7, 1.0)
        center_alpha = max(0.0, min(1.0, brightness_val * 0.9))
        center_color.setAlphaF(center_alpha)

        # Transparent edges
        edge_color = QColor.fromHsvF(hue, 0.8, 0.7)
        edge_alpha = max(0.0, min(1.0, brightness_val * 0.1))
        edge_color.setAlphaF(edge_alpha)

        gradient.setColorAt(0.0, center_color)
        gradient.setColorAt(0.5, edge_color)
        gradient.setColorAt(1.0, QColor(0, 0, 0, 0))

        p.setPen(QPen(QColor(0, 0, 0, 0)))
        p.setBrush(gradient)
        p.drawEllipse(QPointF(x, y), size, size)

        # Draw brighter core
        core_size = size * 0.4
        core_color = QColor.fromHsvF(hue, 0.4, 1.0)
        core_alpha = max(0.0, min(1.0, brightness_val * 0.8))
        core_color.setAlphaF(core_alpha)
        p.setBrush(core_color)
        p.drawEllipse(QPointF(x, y), core_size, core_size)
