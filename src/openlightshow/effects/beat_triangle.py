from PySide6.QtCore import QSize, QPointF
from PySide6.QtGui import QPainter, QColor, QPen
from ..effect_base import Effect
import time


class BeatTriangle(Effect):
    """
    BeatTriangle effect:
    - A triangle with 5px wide lines
    - 10px margin from screen borders
    - Base line alternates between top and bottom every 4 beats
    - Bright neon colors that change based on mid and high frequencies
    - White discs (6px diameter) at the corners
    - Corner discs pulse to 20px diameter on each beat
    - Painter state is isolated with save/restore
    """
    name = "BeatTriangle"
    effect_class = "centereffect_class04"

    def __init__(self, size: QSize):
        super().__init__(size)
        self.size = size

        # Triangle properties
        self.margin = 10
        self.line_width = 5

        # Color state
        self.triangle_color = QColor(0, 255, 255)  # Start with cyan

        # Corner disc properties
        self.normal_disc_radius = 3  # 6px diameter (radius = diameter/2)
        self.flash_disc_radius = 10  # 20px diameter (radius = diameter/2)
        self.current_disc_radius = self.normal_disc_radius

        # Beat flash state
        self.is_flashing = False
        self.flash_duration_ms = 150  # How long the flash lasts
        self.last_beat_time = -1000  # Initialize to allow first beat
        self.beat_cooldown_ms = 300  # 300ms debounce to prevent double beats

        # Triangle orientation state
        self.base_on_top = True  # True = base on top, False = base on bottom
        self.beat_counter = 0  # Count beats to switch orientation

    def resize(self, size: QSize):
        super().resize(size)
        self.size = size

    def on_beat(self):
        """Trigger corner disc flash on beat and handle orientation switching."""
        super().on_beat()
        now = time.time() * 1000
        if now - self.last_beat_time >= self.beat_cooldown_ms:
            self.is_flashing = True
            self.last_beat_time = now

            # Increment beat counter
            self.beat_counter += 1

            # Switch orientation every 8 beats (on beat 8, 16, 24, etc.)
            if self.beat_counter % 8 == 0:
                self.base_on_top = not self.base_on_top

    def update(self, dt_ms: int, energies: dict, sensitivity: float, flash_thresh: float):
        """Update animation state based on time and audio."""
        # Update triangle color based on mid and high frequencies
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

        self.triangle_color = QColor.fromHsvF(hue, saturation, value)

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
        """Draw the BeatTriangle effect."""
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)

        # Calculate screen dimensions with margin
        x1 = self.margin
        y1 = self.margin
        x2 = self.size.width() - self.margin
        y2 = self.size.height() - self.margin

        # Calculate triangle corners based on orientation
        if self.base_on_top:
            # Base on top, apex at bottom center
            left_corner = QPointF(x1, y1)
            right_corner = QPointF(x2, y1)
            apex = QPointF((x1 + x2) / 2, y2)
        else:
            # Base on bottom, apex at top center
            left_corner = QPointF(x1, y2)
            right_corner = QPointF(x2, y2)
            apex = QPointF((x1 + x2) / 2, y1)

        corners = [left_corner, right_corner, apex]

        # Draw the triangle frame with neon color
        triangle_color = QColor(self.triangle_color)
        triangle_color.setAlphaF(max(0.0, min(1.0, brightness)))

        pen = QPen(triangle_color)
        pen.setWidth(self.line_width)
        painter.setPen(pen)
        painter.setBrush(QColor(0, 0, 0, 0))  # No fill, just the outline

        # Draw triangle lines
        painter.drawLine(corners[0], corners[1])  # Base
        painter.drawLine(corners[1], corners[2])  # Right side
        painter.drawLine(corners[2], corners[0])  # Left side

        # Draw white corner discs
        white_color = QColor(255, 255, 255)
        white_color.setAlphaF(max(0.0, min(1.0, brightness)))
        painter.setBrush(white_color)
        painter.setPen(QColor(0, 0, 0, 0))  # No outline for discs

        # Draw disc at each corner
        for corner in corners:
            painter.drawEllipse(corner, self.current_disc_radius, self.current_disc_radius)

        painter.restore()
