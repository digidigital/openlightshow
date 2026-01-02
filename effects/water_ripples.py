from typing import Dict
from PySide6.QtCore import QPointF
from PySide6.QtCore import QSize
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtGui import QPainter, QColor
from PySide6.QtGui import QPen
from ..effect_base import Effect
import random


class WaterRipples(Effect):
    """
    WaterRipples Effect:
    - A new ripple spawns on every beat.
    - At most 4 ripples exist at once; when a new one spawns and there are already 4,
      the oldest ripple is deleted.
    - Ripples expand and fade over time, but never leave the screen (center shifts inward).
    - Robust beat filter prevents spurious multiple triggers.
    - Brighter visuals via additive blending and boosted alpha.
    """

    name = "WaterRipples"
    effect_class = "centereffect_class03"

    def __init__(self, size: QSize):
        super().__init__(size)
        self.size = size
        self.ripples: List[Dict] = []
        self.base_color = QColor(255, 255, 255)

        # Beat filter
        self.time_since_last_beat = 0
        self.min_beat_interval_ms = 250

    def resize(self, size: QSize):
        self.size = size

    def on_beat(self):
        if self.time_since_last_beat < self.min_beat_interval_ms:
            return
        self.time_since_last_beat = 0

        # Spawn new ripple
        x = random.uniform(0, self.size.width())
        y = random.uniform(0, self.size.height())
        self.ripples.append({
            "pos": QPointF(x, y),
            "radius": 0.0,
            "alpha": 255.0,
        })

        # Keep only the 4 most recent ripples
        if len(self.ripples) > 4:
            self.ripples.pop(0)

    def update(self, dt_ms: int, energies: Dict[str, float], sensitivity: float, strobe_thresh: float):
        self.time_since_last_beat += dt_ms

        speed = 0.15 * (1.0 + energies.get("low", 0.0) * sensitivity)
        fade_speed = 18.0  # slower fade for brighter persistence

        for ripple in self.ripples:
            ripple["radius"] += speed * dt_ms
            ripple["alpha"] -= (fade_speed * dt_ms) / 1000.0

            # Keep ripple fully inside screen
            x, y = ripple["pos"].x(), ripple["pos"].y()
            r = ripple["radius"]
            if x - r < 0: x = r
            if x + r > self.size.width(): x = self.size.width() - r
            if y - r < 0: y = r
            if y + r > self.size.height(): y = self.size.height() - r
            ripple["pos"] = QPointF(x, y)

        # Color influenced by frequency bands, boosted
        r = int(min(255, 255 * min(1.0, energies.get("low", 0.0) * sensitivity) * 1.25))
        g = int(min(255, 255 * min(1.0, energies.get("mid", 0.0) * sensitivity) * 1.25))
        b = int(min(255, 255 * min(1.0, energies.get("high", 0.0) * sensitivity) * 1.25))
        self.base_color = QColor(r, g, b)

    def paint(self, p: QPainter, brightness: float):
        if not self.ripples:
            return

        p.save()
        p.setRenderHint(QPainter.Antialiasing, True)
        p.setCompositionMode(QPainter.CompositionMode_Plus)  # additive glow

        for ripple in self.ripples:
            color = QColor(self.base_color)
            alpha = max(0, min(255, int(ripple["alpha"] * brightness * 2.5)))
            color.setAlpha(alpha)
            pen = QPen(color)
            pen.setWidth(5)  # thicker for more light
            p.setPen(pen)
            p.setBrush(Qt.NoBrush)
            p.drawEllipse(ripple["pos"], ripple["radius"], ripple["radius"])

        p.restore()
