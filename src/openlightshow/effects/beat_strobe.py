"""
BeatStrobe effect - Double flash on every beat.

On every beat, generates a light-gray double flash:
- Each flash lasts 10ms 
- Gap between flashes: 50ms (1/20 second)
- Flash fills entire screen with gray
- 200ms beat debouncing to prevent double-triggering
"""

import time
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QPainter, QColor
from ..effect_base import Effect


class BeatStrobe(Effect):
    """
    Double flash strobe effect triggered by beats.

    Fills the entire screen with light gray in two quick pulses
    separated by a brief gap. The effect sequence is:
    - Flash 1: 100ms
    - Gap: 50ms
    - Flash 2: 100ms
    - Total duration: 250ms
    """

    name = "Beat Strobe"
    effect_class = "flash_class01"

    # Timing constants (in seconds)
    FLASH_DURATION = 0.0100  # 10ms 
    FLASH_GAP = 0.050       # 50ms = 1/20 second
    BEAT_DEBOUNCE = 0.200   # 200ms damping time

    def __init__(self, size: QSize):
        super().__init__(size)
        self.flash_state = 0  # 0=off, 1=first flash, 2=gap, 3=second flash
        self.flash_timer = 0.0
        self.last_beat_time = 0.0
        self.gray_color = QColor(200, 200, 200)  # Light gray

    def on_beat(self):
        """Trigger double flash sequence on beat (with debouncing)."""
        current_time = time.time()

        # Check if enough time has passed since last beat (170ms debounce)
        if current_time - self.last_beat_time >= self.BEAT_DEBOUNCE:
            self.flash_state = 1  # Start first flash
            self.flash_timer = 0.0
            self.last_beat_time = current_time

    def update(self, dt_ms: int, energies: dict, sensitivity: float, flash_thresh: float):
        """Update flash sequence timing."""
        if self.flash_state == 0:
            return  # Nothing to do

        dt_sec = dt_ms / 1000.0
        self.flash_timer += dt_sec

        # State machine for double flash sequence
        if self.flash_state == 1:  # First flash
            if self.flash_timer >= self.FLASH_DURATION:
                self.flash_state = 2  # Move to gap
                self.flash_timer = 0.0

        elif self.flash_state == 2:  # Gap between flashes
            if self.flash_timer >= self.FLASH_GAP:
                self.flash_state = 3  # Move to second flash
                self.flash_timer = 0.0

        elif self.flash_state == 3:  # Second flash
            if self.flash_timer >= self.FLASH_DURATION:
                self.flash_state = 0  # End sequence
                self.flash_timer = 0.0

    def paint(self, p: QPainter, brightness: float):
        """Paint the flash if active."""
        p.save()

        # Only draw during flash states (1 and 3), not during gap (2) or off (0)
        if self.flash_state == 1 or self.flash_state == 3:
            # Fill entire screen with light gray
            color = QColor(self.gray_color)
            # Apply brightness multiplier (clamped to valid alpha range)
            alpha = max(0.0, min(1.0, brightness))
            color.setAlphaF(alpha)

            # Fill the entire screen
            p.fillRect(0, 0, self.size.width(), self.size.height(), color)

        p.restore()
