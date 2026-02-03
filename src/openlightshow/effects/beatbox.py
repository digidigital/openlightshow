from PySide6.QtCore import QSize, QPointF
from PySide6.QtGui import QPainter, QColor, QPen
from ..effect_base import Effect
import time


class BeatBox(Effect):
    """
    BeatBox effect:
    - A static rectangle frame with 5px wide lines
    - 10px margin from screen borders
    - Bright neon colors that change based on mid and high frequencies
    - White discs (6px diameter) positioned at the corners
    - Corner discs pulse to 20px diameter on each beat
    - Painter state is isolated with save/restore
    """
    name = "BeatBox"
    effect_class = "centereffect_class04"

    def __init__(self, size: QSize):
        super().__init__(size)
        self.size = size

        # Rectangle properties
        self.margin = 10
        self.line_width = 5

        # Color state
        self.box_color = QColor(0, 255, 255)  # Start with cyan

        # Corner disc properties
        self.normal_disc_radius = 3  # 6px diameter (radius = diameter/2)
        self.flash_disc_radius = 10  # 20px diameter (radius = diameter/2)
        self.current_disc_radius = self.normal_disc_radius

        # Beat flash state
        self.is_flashing = False
        self.flash_duration_ms = 150  # How long the flash lasts
        self.last_beat_time = 0
        self.beat_cooldown_ms = 100  # Minimum time between beat responses

    def resize(self, size: QSize):
        super().resize(size)
        self.size = size

    def on_beat(self):
        """Trigger corner disc flash on beat."""
        super().on_beat()
        now = time.time() * 1000
        if now - self.last_beat_time >= self.beat_cooldown_ms:
            self.is_flashing = True
            self.last_beat_time = now

    def update(self, dt_ms: int, energies: dict, sensitivity: float, flash_thresh: float):
        """Update animation state based on time and audio."""
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
        """Draw the BeatBox effect."""
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)

        # Calculate rectangle bounds (with margin)
        x1 = self.margin
        y1 = self.margin
        x2 = self.size.width() - self.margin
        y2 = self.size.height() - self.margin

        # Draw the rectangle frame with neon color
        box_color = QColor(self.box_color)
        box_color.setAlphaF(max(0.0, min(1.0, brightness)))

        pen = QPen(box_color)
        pen.setWidth(self.line_width)
        painter.setPen(pen)
        painter.setBrush(QColor(0, 0, 0, 0))  # No fill, just the outline

        # Draw rectangle
        painter.drawRect(x1, y1, x2 - x1, y2 - y1)

        # Draw white corner discs
        white_color = QColor(255, 255, 255)
        white_color.setAlphaF(max(0.0, min(1.0, brightness)))
        painter.setBrush(white_color)
        painter.setPen(QColor(0, 0, 0, 0))  # No outline for discs

        # Corner positions (centers of the rectangle corners)
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
