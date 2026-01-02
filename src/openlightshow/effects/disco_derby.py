"""
DiscoDerby effect - Emulates a derby projector with moving colored rectangles.

Features:
- 10 rectangles, each 100px high and 1/10 screen width
- Alternating movement: odd rectangles (1,3,5,7,9) move upward, even (2,4,6,8,10) move downward
- Rectangles start and end outside visible screen (continuous pass-through)
- Triggers only on every 8th beat
- Animation duration: 2x the time between beats
- 180ms debounce to prevent double-triggering
- Random neon colors: red, green, or blue (same color for all rectangles per pass)
"""

import time
import random
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QPainter, QColor, QPen, QBrush
from ..effect_base import Effect


class DiscoDerby(Effect):
    """
    Derby projector effect with alternating rectangle movement.

    Creates a visual effect similar to a derby lighting fixture where
    colored rectangles sweep across the screen in opposite directions.
    """

    name = "Disco Derby"
    effect_class = "derbyeffect_class01"

    # Constants
    NUM_RECTANGLES = 10
    RECT_HEIGHT = 100
    BEAT_DEBOUNCE = 0.180  # 180ms debounce
    DEFAULT_BPM = 120
    DEFAULT_BEAT_INTERVAL = 60.0 / DEFAULT_BPM  # 0.5 seconds at 120 BPM

    # Neon colors
    NEON_RED = QColor(255, 0, 60)
    NEON_GREEN = QColor(0, 255, 60)
    NEON_BLUE = QColor(0, 60, 255)
    COLORS = [NEON_RED, NEON_GREEN, NEON_BLUE]

    def __init__(self, size: QSize):
        super().__init__(size)
        self.rect_width = 0
        self.animation_progress = 0.0  # 0.0 to 1.0
        self.animation_active = False
        self.animation_duration = self.DEFAULT_BEAT_INTERVAL * 4  # 4x duration (doubled from 2x)
        self.last_beat_time = 0.0
        self.current_color = random.choice(self.COLORS)
        self.last_beat_interval = self.DEFAULT_BEAT_INTERVAL
        self.beat_counter = 0  # Count beats to trigger on every 4th

        # Calculate rectangle positions
        self._update_dimensions()

    def _update_dimensions(self):
        """Update rectangle dimensions based on screen size."""
        self.rect_width = self.size.width() // self.NUM_RECTANGLES
        # Calculate travel distance (from above screen to below, or vice versa)
        self.travel_distance = self.size.height() + 2 * self.RECT_HEIGHT

    def resize(self, size: QSize):
        """Handle window resize."""
        super().resize(size)
        self._update_dimensions()

    def on_beat(self):
        """Trigger new animation only on every 4th beat (with debouncing)."""
        current_time = time.time()

        # Check debounce
        if current_time - self.last_beat_time >= self.BEAT_DEBOUNCE:
            # Calculate beat interval for animation duration
            if self.last_beat_time > 0:
                beat_interval = current_time - self.last_beat_time
                # Use measured interval if reasonable (between 0.2s and 2.0s)
                if 0.2 <= beat_interval <= 2.0:
                    self.last_beat_interval = beat_interval

            self.last_beat_time = current_time

            # Increment beat counter
            self.beat_counter += 1

            # Only trigger animation on every 4th beat
            if self.beat_counter >= 8:
                self.beat_counter = 0  # Reset counter

                # Start new animation with 2x beat duration
                self.animation_active = True
                self.animation_progress = 0.0
                self.animation_duration = self.last_beat_interval * 2
                self.current_color = random.choice(self.COLORS)

    def update(self, dt_ms: int, energies: dict, sensitivity: float, flash_thresh: float):
        """Update animation progress."""
        if not self.animation_active:
            return

        dt_sec = dt_ms / 1000.0

        # Update progress
        self.animation_progress += dt_sec / self.animation_duration

        # Check if animation completed
        if self.animation_progress >= 1.0:
            self.animation_active = False
            self.animation_progress = 0.0

    def paint(self, p: QPainter, brightness: float):
        """Paint the moving rectangles."""
        p.save()

        if not self.animation_active:
            p.restore()
            return

        # Ensure dimensions are valid - recalculate if size changed
        if self.rect_width != self.size.width() // self.NUM_RECTANGLES:
            self._update_dimensions()

        # Set up color with brightness
        color = QColor(self.current_color)
        alpha = max(0.0, min(1.0, brightness))
        color.setAlphaF(alpha)
        p.setBrush(QBrush(color))
        p.setPen(Qt.NoPen)  # No border

        # Draw all 10 rectangles
        for i in range(self.NUM_RECTANGLES):
            x = i * self.rect_width

            # Determine direction: odd indices (0,2,4,6,8) go up, even (1,3,5,7,9) go down
            # Note: array index 0 = rectangle 1, so we check if i is even for upward movement
            moves_upward = (i % 2 == 0)

            if moves_upward:
                # Start below screen, move upward
                # Start position: below screen (size.height() + RECT_HEIGHT)
                # End position: above screen (-RECT_HEIGHT)
                start_y = self.size.height() + self.RECT_HEIGHT
                end_y = -self.RECT_HEIGHT
                y = start_y + (end_y - start_y) * self.animation_progress
            else:
                # Start above screen, move downward
                # Start position: above screen (-RECT_HEIGHT)
                # End position: below screen (size.height() + RECT_HEIGHT)
                start_y = -self.RECT_HEIGHT
                end_y = self.size.height() + self.RECT_HEIGHT
                y = start_y + (end_y - start_y) * self.animation_progress

            # Draw rectangle
            p.fillRect(
                int(x),
                int(y),
                int(self.rect_width),
                int(self.RECT_HEIGHT),
                color
            )

        p.restore()
