from PySide6.QtCore import QSize
from PySide6.QtGui import QPainter, QColor, QPen
from ..effect_base import Effect


class MusicVisualizer(Effect):
    """
    MusicVisualizer effect:
    - Horizontal lines that wave up/down based on frequencies
    - Each band pushes a short horizontal line up to screen height
    - Uses half screen width, mirrored at center
    - Low frequencies on the outside, highs in the middle
    - Smooth waving motion
    - Painter state is isolated with save/restore
    """
    name = "MusicVisualizer"
    effect_class = "centereffect_class05"

    def __init__(self, size: QSize):
        super().__init__(size)
        self.size = size

        # Visualizer properties
        self.line_width = 4
        self.num_bands = 16  # Number of frequency bands per half

        # Calculate band positions
        self.half_width = size.width() / 2
        self.band_width = self.half_width / self.num_bands

        # Horizontal line length (short lines)
        self.h_line_length = self.band_width * 0.8  # 80% of band width

        # Energy levels for each band (0.0 - 1.0)
        self.band_levels = [0.0] * self.num_bands

        # Smoothing factors
        self.rise_speed = 8.0  # How fast bars rise
        self.fall_speed = 3.0  # How fast bars fall (slower for smoother look)

        # Colors for different frequency ranges
        self.low_color = QColor.fromHsvF(0.0, 1.0, 1.0)    # Red
        self.mid_color = QColor.fromHsvF(0.33, 1.0, 1.0)   # Green
        self.high_color = QColor.fromHsvF(0.6, 1.0, 1.0)   # Blue/Cyan

    def resize(self, size: QSize):
        super().resize(size)
        self.size = size
        self.half_width = size.width() / 2
        self.band_width = self.half_width / self.num_bands
        self.h_line_length = self.band_width * 0.8

    def update(self, dt_ms: int, energies: dict, sensitivity: float, flash_thresh: float):
        """Update visualizer bars based on audio frequencies."""
        dt_sec = dt_ms / 1000.0

        # Get frequency energies
        low = energies.get('low', 0.0)
        mid = energies.get('mid', 0.0)
        high = energies.get('high', 0.0)

        # Apply sensitivity
        low *= sensitivity
        mid *= sensitivity
        high *= sensitivity

        # Distribute frequencies across bands
        # Low frequencies: outer bands (0-5)
        # Mid frequencies: middle bands (6-10)
        # High frequencies: inner bands (11-15)

        for i in range(self.num_bands):
            # Calculate target energy for this band
            if i < 6:
                # Low frequency bands (outer)
                # Gradually decrease from full low to zero
                target = low * (1.0 - (i / 6.0))
            elif i < 11:
                # Mid frequency bands (middle)
                # Peak in the middle of this range
                mid_pos = (i - 6) / 5.0
                target = mid * (1.0 - abs(mid_pos - 0.5) * 2.0)
            else:
                # High frequency bands (inner)
                # Gradually increase towards center
                high_pos = (i - 11) / 5.0
                target = high * high_pos

            # Clamp target
            target = max(0.0, min(1.0, target))

            # Smooth transition to target
            if target > self.band_levels[i]:
                # Rise quickly
                self.band_levels[i] += (target - self.band_levels[i]) * self.rise_speed * dt_sec
            else:
                # Fall slowly
                self.band_levels[i] += (target - self.band_levels[i]) * self.fall_speed * dt_sec

            # Clamp final value
            self.band_levels[i] = max(0.0, min(1.0, self.band_levels[i]))

    def paint(self, painter: QPainter, brightness: float):
        """Draw the MusicVisualizer effect with horizontal waving lines."""
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)

        # Screen center
        center_x = self.size.width() / 2
        screen_height = self.size.height()

        # Draw each band (left and right mirrored)
        for i in range(self.num_bands):
            level = self.band_levels[i]

            # Calculate y position (height from bottom, maximum is screen height)
            # Line starts at bottom and waves up based on level
            y_position = screen_height - (level * screen_height)

            # Determine color based on frequency range
            if i < 6:
                # Low frequencies - Red
                bar_color = QColor(self.low_color)
            elif i < 11:
                # Mid frequencies - Green
                bar_color = QColor(self.mid_color)
            else:
                # High frequencies - Blue/Cyan
                bar_color = QColor(self.high_color)

            # Apply brightness
            bar_color.setAlphaF(max(0.0, min(1.0, brightness)))

            pen = QPen(bar_color)
            pen.setWidth(self.line_width)
            painter.setPen(pen)

            # Calculate x positions for left and right bars
            # Left side: from center going left
            left_x_center = center_x - (i * self.band_width) - self.band_width / 2

            # Right side: from center going right (mirrored)
            right_x_center = center_x + (i * self.band_width) + self.band_width / 2

            # Calculate horizontal line endpoints
            half_h_length = self.h_line_length / 2

            # Draw horizontal line at the y_position (left side)
            painter.drawLine(
                int(left_x_center - half_h_length),
                int(y_position),
                int(left_x_center + half_h_length),
                int(y_position)
            )

            # Draw horizontal line at the y_position (right side, mirrored)
            painter.drawLine(
                int(right_x_center - half_h_length),
                int(y_position),
                int(right_x_center + half_h_length),
                int(y_position)
            )

        painter.restore()
