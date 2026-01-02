import time
import random
import math
from PySide6.QtCore import QSize, QPointF, Qt
from PySide6.QtGui import QPainter, QColor, QPen
from ..effect_base import Effect


class OrbitalRings(Effect):
    """
    OrbitalRings Effect:
    - Concentric rings expand from center like ripples
    - New rings spawn ONLY on beats (with 170ms debounce)
    - Ring thickness responds to bass
    - Rings travel at 2x base speed and reach screen borders
    - Rings fade out as they expand
    """

    name = "Orbital Rings"
    effect_class = "centereffect_class03"

    def __init__(self, size: QSize):
        super().__init__(size)
        self.rings = []  # list of dicts: {"radius": float, "alpha": float, "color": QColor, "max_radius": float}
        self.max_rings = 4

        # Beat debounce
        self.last_beat_time = 0.0
        self.beat_debounce_ms = 200

        # Energy tracking
        self.bass_energy = 0.0
        self.mid_energy = 0.0

        # Speed multiplier (2x base speed)
        self.speed_multiplier = 3.0

    def resize(self, size: QSize):
        """Update size and recalculate max radius."""
        super().resize(size)

    def on_beat(self):
        # Debounce: ignore beats too close together
        now = time.time() * 250.0
        if now - self.last_beat_time < self.beat_debounce_ms:
            return
        self.last_beat_time = now

        super().on_beat()

        # Calculate max radius to reach screen borders (diagonal distance)
        w, h = self.size.width(), self.size.height()
        max_radius = math.sqrt((w/2)**2 + (h/2)**2)

        # Spawn a new ring - ONLY on beats
        new_ring = {
            "radius": 0.0,
            "alpha": 1.0,
            "color": QColor(self.color),
            "max_radius": max_radius
        }
        self.rings.append(new_ring)

        # Limit number of rings
        while len(self.rings) > self.max_rings:
            self.rings.pop(0)

    def update(self, dt_ms, energies, sensitivity, flash_thresh):
        # Track energies (for line width)
        self.bass_energy = energies.get('low', 0.0) * sensitivity
        self.mid_energy = energies.get('mid', 0.0) * sensitivity

        # Base expansion speed (2x the original 100 = 200 pixels/second)
        base_speed = 200.0 * self.speed_multiplier

        # Update all rings
        dt_sec = dt_ms / 1000.0
        for ring in self.rings[:]:
            # Expand radius at constant speed (not energy-dependent during update)
            ring["radius"] += base_speed * dt_sec

            # Fade out based on distance traveled (reach border = fully faded)
            if ring["max_radius"] > 0:
                fade_progress = ring["radius"] / ring["max_radius"]
                ring["alpha"] = max(0.0, 1.0 - fade_progress)

            # Remove rings that have reached or passed the border
            if ring["radius"] >= ring["max_radius"]:
                self.rings.remove(ring)

    def paint(self, p: QPainter, brightness: float):
        if not self.rings:
            return

        p.save()
        p.setRenderHint(QPainter.Antialiasing, True)

        w, h = self.size.width(), self.size.height()
        cx, cy = w / 2, h / 2

        # Calculate line width based on bass energy
        base_width = 2.0
        line_width = base_width + (self.bass_energy * 8.0)

        for ring in self.rings:
            color = QColor(ring["color"])
            alpha = max(0.0, min(1.0, ring["alpha"] * brightness))
            color.setAlphaF(alpha)

            pen = QPen(color, max(1.0, line_width))
            p.setPen(pen)
            p.setBrush(Qt.NoBrush)

            radius = ring["radius"]
            if radius > 0:
                p.drawEllipse(QPointF(cx, cy), radius, radius)

        p.restore()
