from PySide6.QtCore import QSize, QPointF
from PySide6.QtGui import QPainter, QColor, QPen
from ..effect_base import Effect
import math
import time


class HeartBeatHexagon(Effect):
    """
    HeartBeatHexagon effect:
    - A fast rotating hexagon made of 6 lines (4px wide)
    - Lines are half the screen size
    - Colors change based on music frequencies
    - Lines pulse outward on beats, then slowly return
    - Each line maintains its length and rotational position
    - Painter state is isolated with save/restore
    """
    name = "HeartBeatHexagon"
    effect_class = "centereffect_class03"

    def __init__(self, size: QSize):
        super().__init__(size)
        self.size = size
        self.center = QPointF(size.width() / 2, size.height() / 2)

        # Hexagon properties
        self.num_sides = 6
        self.line_width = 4

        # Calculate base radius (half of smallest screen dimension)
        self.base_radius = min(size.width(), size.height()) / 4
        # Maximum displacement - keep lines on screen
        # Calculate diagonal distance from center to corner
        max_screen_distance = math.sqrt((size.width()/2)**2 + (size.height()/2)**2)
        # Max displacement should keep the line endpoints on screen
        self.max_displacement = max_screen_distance - self.base_radius - 20  # 20px safety margin
        self.max_displacement = max(50, min(self.max_displacement, 200))  # Clamp between 50-200px

        # Current displacement for each line (0 = at base position)
        self.line_displacements = [0.0] * self.num_sides

        # Rotation
        self.rotation_angle = 0.0
        self.rotation_speed = 0.003  # radians per millisecond (fast rotation)

        # Color
        self.hexagon_color = QColor(0, 255, 255)  # Start with cyan

        # Beat pulse mechanics
        self.pulse_speed = 150.0  # pixels per second outward on beat
        self.return_speed = 480.0  # pixels per second returning to base (ultra fast pumping)
        self.beat_cooldown_ms = 300  # 300ms debounce to prevent double beats
        self.last_beat_time = -1000  # Initialize to allow first beat

    def resize(self, size: QSize):
        super().resize(size)
        self.size = size
        self.center = QPointF(size.width() / 2, size.height() / 2)
        self.base_radius = min(size.width(), size.height()) / 4

        # Recalculate max displacement
        max_screen_distance = math.sqrt((size.width()/2)**2 + (size.height()/2)**2)
        self.max_displacement = max_screen_distance - self.base_radius - 20
        self.max_displacement = max(50, min(self.max_displacement, 200))

    def on_beat(self):
        """Trigger line pulse on beat."""
        super().on_beat()
        now = time.time() * 1000
        if now - self.last_beat_time >= self.beat_cooldown_ms:
            # Pulse all lines outward
            for i in range(self.num_sides):
                # Add pulse, but don't exceed maximum
                self.line_displacements[i] = min(
                    self.line_displacements[i] + 200,  # Add 200px displacement (massive pulse)
                    self.max_displacement
                )
            self.last_beat_time = now

    def update(self, dt_ms: int, energies: dict, sensitivity: float, flash_thresh: float):
        """Update animation state based on time and audio."""
        dt_sec = dt_ms / 1000.0

        # Update rotation
        self.rotation_angle += self.rotation_speed * dt_ms
        # Keep angle in reasonable range to prevent overflow
        if self.rotation_angle > 2 * math.pi:
            self.rotation_angle -= 2 * math.pi

        # Update line displacements - slowly return to base position
        for i in range(self.num_sides):
            if self.line_displacements[i] > 0:
                self.line_displacements[i] -= self.return_speed * dt_sec
                # Clamp to 0 minimum
                self.line_displacements[i] = max(0.0, self.line_displacements[i])

        # Update color based on music frequencies
        low = energies.get('low', 0.0)
        mid = energies.get('mid', 0.0)
        high = energies.get('high', 0.0)

        # Create dynamic colors that respond to music
        # Use different frequency bands for different hue ranges
        total_energy = low + mid + high
        if total_energy > 0.1:
            # Mix hues based on frequency dominance
            if high > mid and high > low:
                # High frequencies - cyan/blue spectrum
                hue = 0.5 + (high * 0.15)  # 0.5-0.65 (180°-234°)
            elif mid > low:
                # Mid frequencies - green/yellow spectrum
                hue = 0.3 + (mid * 0.15)  # 0.3-0.45 (108°-162°)
            else:
                # Low frequencies - red/magenta spectrum
                hue = 0.0 + (low * 0.1)  # 0.0-0.1 (0°-36°)
        else:
            hue = 0.5  # Default cyan

        # Keep saturation high for neon effect
        saturation = 1.0
        # Value responds to total energy
        value = max(0.0, min(1.0, 0.7 + total_energy * 0.3 * sensitivity))

        # Clamp all HSV values
        hue = max(0.0, min(0.99, hue))

        self.hexagon_color = QColor.fromHsvF(hue, saturation, value)

    def paint(self, painter: QPainter, brightness: float):
        """Draw the HeartBeatHexagon effect."""
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)

        # Set up color with brightness
        line_color = QColor(self.hexagon_color)
        line_color.setAlphaF(max(0.0, min(1.0, brightness)))

        pen = QPen(line_color)
        pen.setWidth(self.line_width)
        painter.setPen(pen)

        # Calculate the original hexagon line length (side length)
        side_angle = 2 * math.pi / self.num_sides
        # Line length using the law of cosines for hexagon side
        line_length = 2 * self.base_radius * math.sin(side_angle / 2)

        # Draw each hexagon line
        for i in range(self.num_sides):
            # Calculate angle for this line's center direction
            angle = self.rotation_angle + (i * 2 * math.pi / self.num_sides)

            # Calculate the midpoint angle (center of the line segment)
            midpoint_angle = angle + (side_angle / 2)

            # Calculate displacement distance for this line
            displacement = self.line_displacements[i]
            # Ensure displacement doesn't exceed safe bounds
            displacement = min(displacement, self.max_displacement)

            # Calculate the midpoint position (base position + displacement outward)
            midpoint_radius = self.base_radius + displacement
            midpoint_x = self.center.x() + midpoint_radius * math.cos(midpoint_angle)
            midpoint_y = self.center.y() + midpoint_radius * math.sin(midpoint_angle)

            # Calculate the two endpoints relative to the midpoint
            # The line is perpendicular to the radius at this angle
            perpendicular_angle = midpoint_angle + math.pi / 2

            half_length = line_length / 2
            x1 = midpoint_x + half_length * math.cos(perpendicular_angle)
            y1 = midpoint_y + half_length * math.sin(perpendicular_angle)
            x2 = midpoint_x - half_length * math.cos(perpendicular_angle)
            y2 = midpoint_y - half_length * math.sin(perpendicular_angle)

            # Draw the line
            painter.drawLine(
                int(x1), int(y1),
                int(x2), int(y2)
            )

        painter.restore()
