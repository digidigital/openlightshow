from PySide6.QtCore import QSize, QPointF
from PySide6.QtGui import QPainter, QColor, QPen
from ..effect_base import Effect
import time


class BeatBoxMoving(Effect):
    """
    BeatBoxMoving effect:
    - A rectangle frame with 5px wide lines (half screen width)
    - 10px margin from screen borders
    - Moves from left to right over 4 beats, then back over 4 beats
    - Bright neon colors that change based on mid and high frequencies
    - White discs (6px diameter) at the corners
    - Corner discs pulse to 20px diameter on each beat
    - Painter state is isolated with save/restore
    """
    name = "BeatBoxMoving"
    effect_class = "centereffect_class04"

    def __init__(self, size: QSize):
        super().__init__(size)
        self.size = size

        # Rectangle properties
        self.margin = 10
        self.line_width = 5

        # Box size (half screen width)
        self.box_width = (size.width() - 2 * self.margin) / 2
        self.box_height = size.height() - 2 * self.margin

        # Position tracking
        self.left_position = self.margin  # Starting position (left aligned)
        self.right_position = size.width() - self.margin - self.box_width  # Rightmost position
        self.current_x = self.left_position  # Current x position
        self.target_x = self.left_position  # Target x position

        # Movement tracking
        self.moving_right = True  # Direction of movement
        self.beat_in_cycle = 0  # Beat counter within 4-beat cycle (0-3)

        # Color state
        self.box_color = QColor(0, 255, 255)  # Start with cyan

        # Corner disc properties
        self.normal_disc_radius = 3  # 6px diameter (radius = diameter/2)
        self.flash_disc_radius = 10  # 20px diameter (radius = diameter/2)
        self.current_disc_radius = self.normal_disc_radius

        # Beat flash state
        self.is_flashing = False
        self.flash_duration_ms = 150  # How long the flash lasts
        self.last_beat_time = -1000  # Initialize to allow first beat
        self.beat_cooldown_ms = 300  # 300ms debounce to prevent double beats

    def resize(self, size: QSize):
        super().resize(size)
        self.size = size

        # Recalculate box dimensions and positions
        self.box_width = (size.width() - 2 * self.margin) / 2
        self.box_height = size.height() - 2 * self.margin
        self.left_position = self.margin
        self.right_position = size.width() - self.margin - self.box_width

        # Update current position to maintain relative position
        if self.moving_right:
            progress = self.beat_in_cycle / 4.0
            self.current_x = self.left_position + (self.right_position - self.left_position) * progress
        else:
            progress = self.beat_in_cycle / 4.0
            self.current_x = self.right_position - (self.right_position - self.left_position) * progress

    def on_beat(self):
        """Trigger corner disc flash on beat and handle movement."""
        super().on_beat()
        now = time.time() * 1000
        if now - self.last_beat_time >= self.beat_cooldown_ms:
            self.is_flashing = True
            self.last_beat_time = now

            # Increment beat counter
            self.beat_in_cycle += 1

            # Calculate movement step (divide total distance by 4 beats)
            step_distance = (self.right_position - self.left_position) / 4.0

            if self.moving_right:
                # Moving right: increment position
                if self.beat_in_cycle <= 4:
                    self.target_x = self.left_position + (step_distance * self.beat_in_cycle)

                # After 4 beats, switch direction
                if self.beat_in_cycle >= 4:
                    self.moving_right = False
                    self.beat_in_cycle = 0
                    self.target_x = self.right_position  # Ensure we're at rightmost position
            else:
                # Moving left: decrement position
                if self.beat_in_cycle <= 4:
                    self.target_x = self.right_position - (step_distance * self.beat_in_cycle)

                # After 4 beats, switch direction
                if self.beat_in_cycle >= 4:
                    self.moving_right = True
                    self.beat_in_cycle = 0
                    self.target_x = self.left_position  # Ensure we're at leftmost position

    def update(self, dt_ms: int, energies: dict, sensitivity: float, flash_thresh: float):
        """Update animation state based on time and audio."""
        dt_sec = dt_ms / 1000.0

        # Smoothly interpolate to target position
        # Move 30% of the distance per frame for smooth motion
        interpolation_speed = 8.0  # Higher = faster interpolation
        self.current_x += (self.target_x - self.current_x) * min(1.0, interpolation_speed * dt_sec)

        # Update box color based on mid and high frequencies
        mid = energies.get('mid', 0.0)
        high = energies.get('high', 0.0)

        # Create bright neon colors that respond to music
        # Mix between different neon colors based on frequency content
        if high > mid:
            # High frequencies dominant - use cyan/blue spectrum
            hue = 0.5 + (high * 0.16)  # 0.5-0.66 (180°-237° cyan to blue)
        else:
            # Mid frequencies dominant - use magenta/pink spectrum
            hue = 0.778 + (mid * 0.2)  # 0.778-0.978 (280°-352° magenta to red)

        # Keep saturation and value high for neon effect
        # Clamp hue, saturation, and value to valid range [0.0, 1.0]
        hue = max(0.0, min(1.0, hue))
        saturation = 1.0
        value = max(0.0, min(1.0, 0.8 + (mid + high) * 0.1 * sensitivity))  # Brightness responds to energy

        self.box_color = QColor.fromHsvF(hue, saturation, value)

        # Update flash animation
        if self.is_flashing:
            elapsed = (time.time() * 1000) - self.last_beat_time
            if elapsed < self.flash_duration_ms:
                # Animate from flash to normal size
                progress = elapsed / self.flash_duration_ms
                self.current_disc_radius = self.flash_disc_radius + \
                    (self.normal_disc_radius - self.flash_disc_radius) * progress
            else:
                self.is_flashing = False
                self.current_disc_radius = self.normal_disc_radius
        else:
            self.current_disc_radius = self.normal_disc_radius

    def paint(self, painter: QPainter, brightness: float):
        """Draw the BeatBoxMoving effect."""
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)

        # Calculate rectangle bounds
        x1 = self.current_x
        y1 = self.margin
        x2 = self.current_x + self.box_width
        y2 = self.margin + self.box_height

        # Draw the rectangle frame with neon color
        box_color = QColor(self.box_color)
        box_color.setAlphaF(max(0.0, min(1.0, brightness)))

        pen = QPen(box_color)
        pen.setWidth(self.line_width)
        painter.setPen(pen)
        painter.setBrush(QColor(0, 0, 0, 0))  # No fill, just the outline

        # Draw rectangle
        painter.drawRect(int(x1), int(y1), int(x2 - x1), int(y2 - y1))

        # Draw white corner discs
        white_color = QColor(255, 255, 255)
        white_color.setAlphaF(max(0.0, min(1.0, brightness)))
        painter.setBrush(white_color)
        painter.setPen(QColor(0, 0, 0, 0))  # No outline for discs

        # Corner positions
        corners = [
            QPointF(x1, y1),  # Top-left
            QPointF(x2, y1),  # Top-right
            QPointF(x2, y2),  # Bottom-right
            QPointF(x1, y2),  # Bottom-left
        ]

        # Draw disc at each corner
        for corner in corners:
            painter.drawEllipse(corner, self.current_disc_radius, self.current_disc_radius)

        painter.restore()
