import time
import random
from typing import Dict

from PySide6.QtCore import Qt, QSize, QPointF
from PySide6.QtGui import QPainter, QColor, QPen

from ..effect_base import Effect


class BulletHoles(Effect):
    """
    BulletHoles Effect:
    - On each beat, add exactly two new neon-colored circles.
    - Circles persist between beats.
    - Maximum of 8 circles total.
    - If adding two would exceed 8, remove two RANDOM OLD circles
      (the ones that existed before this beat).
    - New circles created on this beat are never removed on the same beat.
    - Radius = 1/20 of screen height.
    - Line thickness boosted by +2 px for the beat frame only.
    - Includes beat debounce to prevent double-triggering.
    """

    name = "BulletHoles"
    effect_class = "centereffect_class07"

    def __init__(self, size: QSize):
        super().__init__(size)

        self.circles_x = []  # list of dicts: {"nx":..., "ny":..., "color":...}

        self.base_line_width = 2.0
        self.line_width = self.base_line_width
        self.beat_flash = False

        # Beat debounce
        self.last_beat_time = 0.0
        self.beat_debounce_ms = 200

        self.neon_colors = [
            QColor(57, 255, 20),    # neon green
            QColor(199, 21, 133),   # neon purple
            QColor(255, 20, 147),   # neon pink
            QColor(255, 255, 0),    # neon yellow
            QColor(255, 165, 0),    # neon orange
            QColor(0, 255, 255),    # neon cyan
            QColor(255, 0, 255),    # neon magenta
            QColor(0, 255, 128),    # neon lime
        ]

    def resize(self, size: QSize):
        super().resize(size)

    def on_beat(self):
        # Debounce: ignore beats too close together
        now = time.time() * 1000.0
        if now - self.last_beat_time < self.beat_debounce_ms:
            return
        self.last_beat_time = now

        super().on_beat()

        # Boost thickness for this frame only
        self.beat_flash = True
        self.line_width = self.base_line_width + 2.0

        # Snapshot of old circles BEFORE adding new ones
        old_indices = list(range(len(self.circles_x)))

        # Compute safe normalized bounds
        w = max(1, self.size.width())
        h = max(1, self.size.height())
        r_px = max(1.0, h / 20.0)
        nx_min = r_px / w
        nx_max = 1.0 - (r_px / w)
        ny_min = r_px / h
        ny_max = 1.0 - (r_px / h)

        # Create two new circles
        new_circles = []
        for _ in range(2):
            nx = random.uniform(nx_min, nx_max)
            ny = random.uniform(ny_min, ny_max)
            color = random.choice(self.neon_colors)
            new_circles.append({"nx": nx, "ny": ny, "color": color})

        # Add new circles
        self.circles_x.extend(new_circles)

        # Enforce max of 8 by removing two RANDOM OLD ones
        MAX = 8
        if len(self.circles_x) > MAX:
            old_count = len(old_indices)
            remove_count = min(2, old_count)

            # Choose random old ones
            to_remove = random.sample(old_indices, k=remove_count)

            # Remove in descending order so indices stay valid
            for idx in sorted(to_remove, reverse=True):
                if 0 <= idx < len(self.circles_x):
                    self.circles_x.pop(idx)

        # Final safety clamp
        while len(self.circles_x) > MAX:
            self.circles_x.pop(0)

    def update(self, dt_ms, energies, sensitivity, strobe_thresh):
        # Reset thickness after the beat frame
        if self.beat_flash:
            self.beat_flash = False
            self.line_width = self.base_line_width

    def paint(self, p: QPainter, brightness: float):
        p.save()

        w = max(1, self.size.width())
        h = max(1, self.size.height())
        r = max(1.0, h / 20.0)

        for c in self.circles_x:
            cx = c["nx"] * w
            cy = c["ny"] * h

            color = QColor(c["color"])
            color.setAlphaF(max(0.0, min(1.0, float(brightness))))

            pen = QPen(color, max(1.0, self.line_width))
            pen.setCosmetic(True)
            p.setPen(pen)
            p.setBrush(Qt.NoBrush)

            p.drawEllipse(QPointF(cx, cy), r, r)

        p.restore()
