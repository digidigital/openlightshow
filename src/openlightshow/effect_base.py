"""
Base Effect class for the Beamer Lightshow application.

All visual effects must inherit from this class and implement the required methods.
"""

import random
from typing import Dict
from PySide6.QtCore import QSize
from PySide6.QtGui import QPainter, QColor


class Effect:
    """
    Base class for all lightshow effects.

    Attributes:
        name: String identifier for the effect (must be unique)
        effect_class: Classification attribute for grouping similar effects
        size: Current size of the rendering area
        color: Current color of the effect (can change on beats)
    """
    name = "Effect"
    effect_class = "effect_class1"  # Default class, should be overridden in subclasses

    def __init__(self, size: QSize):
        """
        Initialize the effect with the given size.

        Args:
            size: QSize representing the rendering area dimensions
        """
        self.size = size
        self.color = QColor(0, 255, 0)

    def resize(self, size: QSize):
        """
        Called when the rendering area is resized.

        Args:
            size: New QSize for the rendering area
        """
        self.size = size

    def on_beat(self):
        """
        Called when a beat is detected in the music.
        Default behavior: randomize the effect color.
        """
        self.color = QColor(
            random.randint(100, 255),
            random.randint(100, 255),
            random.randint(100, 255)
        )

    def update(self, dt_ms: int, energies: Dict[str, float], sensitivity: float, flash_thresh: float):
        """
        Update effect state (called every frame at ~60 FPS).

        Args:
            dt_ms: Time elapsed since last update in milliseconds
            energies: Dictionary with 'low', 'mid', 'high' frequency band energies (0.0-1.0)
            sensitivity: User-controlled sensitivity multiplier
            flash_thresh: Threshold for high-energy strobe/flash triggers
        """
        pass

    def paint(self, p: QPainter, brightness: float):
        """
        Render the effect using QPainter.

        Args:
            p: QPainter instance for drawing
            brightness: Overall brightness multiplier (0.0-1.0+)
        """
        pass
