"""
ColorfulScanner effect - Rotating colorful tube that scans between screen quadrants.

Behavior:
- Circle with radius of 0.45*h/4 consisting of 16 colorful segments
- Each bright neon segment is followed by slightly darker green, blue, red segments
- The whole circle rotates continuously around its center
- Starts in top-left quadrant center
- On beat: Moves very fast to a random other quadrant's center
- Bass: Controls rotation speed
- Beat: Triggers tube width pulse (4px -> 8px -> 4px) and quadrant jump
"""

import math
import time
import random
from PySide6.QtCore import QPointF, QSize, QRectF
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QConicalGradient
from ..effect_base import Effect


class ColorfulScannerEffect(Effect):
    name = "ColorfulScanner"
    effect_class = "centereffect_class03"

    def __init__(self, size: QSize):
        super().__init__(size)
        self.rotation_angle = 0.0

        # Music reactive values
        self.bass_energy = 0.0
        self.mid_energy = 0.0
        self.high_energy = 0.0

        # Beat detection
        self.last_beat_time = 0.0
        self.beat_pulse = 0.0  # For tube width pulsing

        # Base parameters
        self.base_rotation_speed = 120.0  # Degrees per second (faster rotation)
        self.base_tube_width = 4  # Base tube width in pixels
        self.pulse_tube_width = 8  # Pulsed tube width in pixels

        # Fixed 16 segments with static colors
        self.num_segments = 16
        self.segment_colors = self._generate_static_colors()

        # Quadrant positioning
        self.current_quadrant = 0  # 0=top-left, 1=top-right, 2=bottom-left, 3=bottom-right
        self.target_quadrant = 0
        self.quadrant_transition = 0.0  # 0.0 = at current, 1.0 = at target

        # Current position (center of tube)
        w, h = size.width(), size.height()
        self.current_x = w * 0.25
        self.current_y = h * 0.25
        self.target_x = self.current_x
        self.target_y = self.current_y

    def _generate_static_colors(self):
        """Generate static color pattern: random neon followed by darker RGB."""
        colors = []

        # 16 segments = 4 repetitions of (neon + darker green + darker blue + darker red)
        for _ in range(4):
            # Random bright neon color
            neon_hue = random.random()
            colors.append((neon_hue, 1.0, 1.0))  # Bright neon

            # Followed by slightly darker green, blue, red
            colors.append((0.33, 0.7, 0.7))  # Darker green
            colors.append((0.66, 0.7, 0.7))  # Darker blue
            colors.append((0.0, 0.7, 0.7))   # Darker red

        return colors

    def _get_quadrant_center(self, quadrant):
        """Get the center position for a given quadrant (0-3)."""
        w, h = self.size.width(), self.size.height()

        if quadrant == 0:  # Top-left
            return (w * 0.25, h * 0.25)
        elif quadrant == 1:  # Top-right
            return (w * 0.75, h * 0.25)
        elif quadrant == 2:  # Bottom-left
            return (w * 0.25, h * 0.75)
        else:  # Bottom-right (quadrant == 3)
            return (w * 0.75, h * 0.75)

    def on_beat(self):
        """Triggered on beat detection."""
        current_time = time.time() * 1000.0

        # Debounce beats (200ms)
        if current_time - self.last_beat_time < 200:
            return

        self.last_beat_time = current_time

        # Trigger tube width pulse
        self.beat_pulse = 1.0

        # Jump to a random different quadrant
        other_quadrants = [q for q in range(4) if q != self.target_quadrant]
        self.current_quadrant = self.target_quadrant
        self.target_quadrant = random.choice(other_quadrants)

        # Reset transition
        self.quadrant_transition = 0.0

        # Set new target position
        self.target_x, self.target_y = self._get_quadrant_center(self.target_quadrant)

    def update(self, dt_ms, energies, sensitivity, flash_thresh):
        """Update effect state."""
        dt_sec = dt_ms / 1000.0

        # Extract energy values
        self.bass_energy = energies.get('low', 0.0) * sensitivity
        self.mid_energy = energies.get('mid', 0.0) * sensitivity
        self.high_energy = energies.get('high', 0.0) * sensitivity

        # Update rotation - continuous, bass controls speed
        speed_multiplier = 1.0 + self.bass_energy * 2.0
        rotation_speed = self.base_rotation_speed * speed_multiplier
        self.rotation_angle += rotation_speed * dt_sec
        self.rotation_angle = self.rotation_angle % 360.0

        # Decay beat pulse
        if self.beat_pulse > 0:
            self.beat_pulse -= dt_sec * 5.0  # Fast decay
            self.beat_pulse = max(0.0, self.beat_pulse)

        # Very fast quadrant transition (almost instant)
        if self.quadrant_transition < 1.0:
            self.quadrant_transition += dt_sec * 20.0  # Very fast (20x per second)
            self.quadrant_transition = min(1.0, self.quadrant_transition)

            # Smooth interpolation with easing
            t = self.quadrant_transition
            # Ease-out cubic for snappy movement
            eased_t = 1.0 - pow(1.0 - t, 3)

            # Get start position
            start_x, start_y = self._get_quadrant_center(self.current_quadrant)

            # Interpolate position
            self.current_x = start_x + (self.target_x - start_x) * eased_t
            self.current_y = start_y + (self.target_y - start_y) * eased_t

    def paint(self, p: QPainter, brightness: float):
        """Render the colorful scanner effect."""
        p.save()

        w, h = self.size.width(), self.size.height()

        # Circle radius (simplified calculation: 0.45*h * 5/12 = 0.1875*h)
        radius = h * 0.1875

        # Use current position (interpolated during quadrant transition)
        cx, cy = self.current_x, self.current_y

        # Fixed 16 segments
        angle_per_segment = 360.0 / self.num_segments

        # Tube width with beat pulse (4px -> 8px -> 4px)
        current_tube_width = self.base_tube_width + (self.pulse_tube_width - self.base_tube_width) * self.beat_pulse

        # Draw each segment
        for i in range(self.num_segments):
            # Calculate segment angle
            start_angle = (i * angle_per_segment + self.rotation_angle) % 360.0

            # Get color for this segment (static colors)
            hue, sat, val = self.segment_colors[i]

            # Draw the segment as an arc
            self._draw_segment(p, cx, cy, radius, start_angle, angle_per_segment,
                             hue, sat, val, brightness, current_tube_width)

        p.restore()

    def _draw_segment(self, p: QPainter, cx, cy, radius, start_angle, span_angle,
                     hue, saturation, value, brightness_val, tube_width):
        """Draw a single tube segment."""
        # Calculate inner and outer radius for the tube
        outer_radius = radius
        inner_radius = radius - tube_width

        # Create color for the segment
        color = QColor.fromHsvF(hue, saturation, value)
        color.setAlphaF(max(0.0, min(1.0, brightness_val)))

        # Set up painter
        p.setPen(QPen(QColor(0, 0, 0, 0)))
        p.setBrush(QBrush(color))

        # Draw the segment using a path
        # We'll draw it as a filled arc by drawing the outer arc, then the inner arc in reverse
        from PySide6.QtGui import QPainterPath

        path = QPainterPath()

        # Convert angles to Qt format (Qt uses 1/16th of a degree, and 0° is at 3 o'clock)
        # We need to adjust: our 0° is at 12 o'clock, Qt's 0° is at 3 o'clock
        qt_start_angle = (90.0 - start_angle) * 16.0
        qt_span_angle = -span_angle * 16.0

        # Outer arc
        outer_rect = QRectF(cx - outer_radius, cy - outer_radius,
                           outer_radius * 2, outer_radius * 2)
        path.arcMoveTo(outer_rect, qt_start_angle / 16.0)
        path.arcTo(outer_rect, qt_start_angle / 16.0, qt_span_angle / 16.0)

        # Inner arc (reverse direction)
        inner_rect = QRectF(cx - inner_radius, cy - inner_radius,
                           inner_radius * 2, inner_radius * 2)
        # Calculate end angle for the line to inner arc
        end_angle = qt_start_angle + qt_span_angle
        path.arcTo(inner_rect, end_angle / 16.0, -qt_span_angle / 16.0)

        # Close the path
        path.closeSubpath()

        # Draw the filled segment
        p.drawPath(path)
