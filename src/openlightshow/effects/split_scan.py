from PySide6.QtCore import QSize, QPointF
from PySide6.QtGui import QPainter, QColor, QPen
from ..effect_base import Effect
import random


class SplitScan(Effect):
    """
    SplitScan effect:
    - Two horizontal 4px wide lines scanning vertically
    - Left line scans left half, right line scans right half
    - One starts from top, other from bottom
    - Lines move between top and bottom continuously
    - Colors change randomly and independently based on music
    - 8px diameter discs at line endpoints that move with the lines
    - Painter state is isolated with save/restore
    """
    name = "SplitScan"
    effect_class = "centereffect_class05"

    def __init__(self, size: QSize):
        super().__init__(size)
        self.size = size

        # Line properties
        self.line_width = 4
        self.disc_radius = 4  # 8px diameter

        # Left line (scans left half)
        self.left_y = 0  # Will be set properly in resize
        self.left_direction = 1  # 1 = down, -1 = up
        self.left_color = QColor(0, 255, 255)  # Cyan

        # Right line (scans right half)
        self.right_y = 0  # Will be set properly in resize
        self.right_direction = -1  # -1 = up, 1 = down
        self.right_color = QColor(255, 0, 255)  # Magenta

        # Scan speed (pixels per second) - 6x faster than original
        self.scan_speed = 1200.0

        # Neon colors for random changes
        self.neon_colors = [
            QColor(57, 255, 20),    # neon green
            QColor(255, 20, 147),   # neon pink
            QColor(0, 255, 255),    # neon cyan
            QColor(255, 255, 0),    # neon yellow
            QColor(255, 0, 255),    # neon magenta
            QColor(255, 165, 0),    # neon orange
            QColor(0, 255, 128),    # neon lime
            QColor(255, 50, 255),   # bright purple
            QColor(255, 100, 100),  # bright red
            QColor(100, 255, 255),  # bright cyan
        ]

    def resize(self, size: QSize):
        super().resize(size)
        self.size = size

        # Initialize positions properly based on actual screen size
        # Left line starts at top
        self.left_y = 0
        # Right line starts at bottom
        self.right_y = size.height()

    def update(self, dt_ms: int, energies: dict, sensitivity: float, flash_thresh: float):
        """Update line positions and colors based on music."""
        dt_sec = dt_ms / 1000.0

        # Get frequency energies
        low = energies.get('low', 0.0)
        mid = energies.get('mid', 0.0)
        high = energies.get('high', 0.0)

        # Update left line position
        self.left_y += self.left_direction * self.scan_speed * dt_sec

        # Reverse left line direction when hitting edges
        if self.left_y >= self.size.height():
            self.left_y = self.size.height()
            self.left_direction = -1
            # Change color on direction change based on music energy
            if low > 0.3:
                self.left_color = random.choice(self.neon_colors)
        elif self.left_y <= 0:
            self.left_y = 0
            self.left_direction = 1
            # Change color on direction change based on music energy
            if low > 0.3:
                self.left_color = random.choice(self.neon_colors)

        # Update right line position
        self.right_y += self.right_direction * self.scan_speed * dt_sec

        # Reverse right line direction when hitting edges
        if self.right_y >= self.size.height():
            self.right_y = self.size.height()
            self.right_direction = -1
            # Change color on direction change based on music energy
            if mid > 0.3 or high > 0.3:
                self.right_color = random.choice(self.neon_colors)
        elif self.right_y <= 0:
            self.right_y = 0
            self.right_direction = 1
            # Change color on direction change based on music energy
            if mid > 0.3 or high > 0.3:
                self.right_color = random.choice(self.neon_colors)

    def paint(self, painter: QPainter, brightness: float):
        """Draw the SplitScan effect."""
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)

        # Screen dimensions
        screen_width = self.size.width()
        half_width = screen_width / 2

        # Draw left line (left half of screen)
        left_color = QColor(self.left_color)
        left_color.setAlphaF(max(0.0, min(1.0, brightness)))

        # Draw left horizontal line
        pen = QPen(left_color, self.line_width)
        painter.setPen(pen)
        painter.drawLine(
            int(0),
            int(self.left_y),
            int(half_width),
            int(self.left_y)
        )

        # Draw left line endpoint discs (20% brighter than line)
        left_disc_color = QColor(self.left_color)
        left_disc_color.setAlphaF(max(0.0, min(1.0, brightness * 1.2)))
        painter.setBrush(left_disc_color)
        painter.setPen(QColor(0, 0, 0, 0))  # No outline for discs
        # Keep discs fully on screen by offsetting from edges
        painter.drawEllipse(QPointF(self.disc_radius, self.left_y), self.disc_radius, self.disc_radius)
        painter.drawEllipse(QPointF(half_width, self.left_y), self.disc_radius, self.disc_radius)

        # Draw right line (right half of screen)
        right_color = QColor(self.right_color)
        right_color.setAlphaF(max(0.0, min(1.0, brightness)))

        # Draw right horizontal line
        pen = QPen(right_color, self.line_width)
        painter.setPen(pen)
        painter.drawLine(
            int(half_width),
            int(self.right_y),
            int(screen_width),
            int(self.right_y)
        )

        # Draw right line endpoint discs (20% brighter than line)
        right_disc_color = QColor(self.right_color)
        right_disc_color.setAlphaF(max(0.0, min(1.0, brightness * 1.2)))
        painter.setBrush(right_disc_color)
        painter.setPen(QColor(0, 0, 0, 0))  # No outline for discs
        # Keep discs fully on screen by offsetting from edges
        painter.drawEllipse(QPointF(half_width, self.right_y), self.disc_radius, self.disc_radius)
        painter.drawEllipse(QPointF(screen_width - self.disc_radius, self.right_y), self.disc_radius, self.disc_radius)

        painter.restore()
