import math
import random
from typing import Dict, List, Tuple

from PySide6.QtCore import Qt, QSize, QPointF
from PySide6.QtGui import QPainter, QColor, QPen, QBrush

from ..effect_base import Effect


class FlashyLines(Effect):
    """
    FlashyLines Effect (derived from FlashyHoles):
    - On each beat, spawn up to 2 colorful straight line segments.
    - Each line has length = 1/5 of screen height and base width = 5 px.
    - Lines are placed at random angles and positions but are guaranteed
      not to intersect existing lines (best-effort with retries).
    - A white disc (radius 3 px) is drawn at each line endpoint.
    - Line thickness increases only on the beat frame (+2 px), then resets.
    - Maximum of 8 lines retained.
    - Reacts to audio: mid energy pulses line brightness; low energy slightly
      shifts positions for a subtle wobble when sensitivity > 0.
    """

    name = "FlashyLines"
    effect_class = "centereffect_class07"

    def __init__(self, size: QSize):
        super().__init__(size)
        self.size = size

        # Each line: (x1, y1, x2, y2, QColor)
        self.lines: List[Tuple[float, float, float, float, QColor]] = []

        self.base_line_width = 5
        self.current_line_width = self.base_line_width
        self.beat_flash = False

        self.endpoint_radius = 3.0

        # store last audio state for paint-time reactions
        self.last_energies: Dict[str, float] = {"low": 0.0, "mid": 0.0, "high": 0.0}
        self.last_sensitivity: float = 0.5

        # neon palette
        self.neon_colors = [
            QColor(57, 255, 20),    # neon green
            QColor(199, 21, 133),   # neon purple/pink
            QColor(255, 20, 147),   # neon pink
            QColor(255, 255, 0),    # neon yellow
            QColor(255, 165, 0),    # neon orange
            QColor(0, 255, 255),    # neon cyan
            QColor(255, 0, 255),    # neon magenta
        ]

    def resize(self, size: QSize):
        super().resize(size)
        self.size = size
        # Optionally clear or re-center lines if desired; keep existing lines but ensure they remain valid
        # (we won't reposition existing lines here to avoid jarring jumps)

    def _segments_intersect(self, a1, a2, b1, b2) -> bool:
        """Return True if segment a1-a2 intersects b1-b2 (excluding touching at endpoints)."""
        (x1, y1), (x2, y2) = a1, a2
        (x3, y3), (x4, y4) = b1, b2

        def ccw(p1, p2, p3):
            return (p3[1] - p1[1]) * (p2[0] - p1[0]) > (p2[1] - p1[1]) * (p3[0] - p1[0])

        # Use standard segment intersection test
        A = (x1, y1)
        B = (x2, y2)
        C = (x3, y3)
        D = (x4, y4)

        # If segments share endpoints, consider that non-intersecting for our placement purposes
        shared_endpoint = (
            (A == C) or (A == D) or (B == C) or (B == D)
        )
        if shared_endpoint:
            return False

        return (ccw(A, C, D) != ccw(B, C, D)) and (ccw(A, B, C) != ccw(A, B, D))

    def _valid_line_position(self, x1, y1, x2, y2) -> bool:
        """Check endpoints are inside canvas and do not intersect existing lines."""
        w = self.size.width()
        h = self.size.height()

        # endpoints must be within bounds (allow tiny margin)
        margin = 0.5
        if not (margin <= x1 <= w - margin and margin <= x2 <= w - margin and
                margin <= y1 <= h - margin and margin <= y2 <= h - margin):
            return False

        # check intersection with existing lines
        for (ex1, ey1, ex2, ey2, _) in self.lines:
            if self._segments_intersect((x1, y1), (x2, y2), (ex1, ey1), (ex2, ey2)):
                return False

        return True

    def on_beat(self):
        super().on_beat()

        w = self.size.width()
        h = self.size.height()
        length = h / 5.0  # 1/5th of screen height

        # Mark beat flash and increase thickness for this frame
        self.beat_flash = True
        self.current_line_width = self.base_line_width + 2

        # Try to add up to 2 new non-intersecting lines
        attempts_per_line = 30
        added = 0
        for _ in range(2):
            success = False
            for attempt in range(attempts_per_line):
                # choose a center point with margin so endpoints stay inside
                half = length / 2.0
                cx = random.uniform(half, w - half)
                cy = random.uniform(half, h - half)
                angle = random.uniform(0, 2 * math.pi)
                dx = math.cos(angle) * half
                dy = math.sin(angle) * half
                x1 = cx - dx
                y1 = cy - dy
                x2 = cx + dx
                y2 = cy + dy

                if self._valid_line_position(x1, y1, x2, y2):
                    color = random.choice(self.neon_colors)
                    self.lines.append((x1, y1, x2, y2, color))
                    added += 1
                    success = True
                    break
            if not success:
                # couldn't place this line without intersection after many tries; skip it
                continue

        # Enforce maximum of 8 lines (remove oldest)
        while len(self.lines) > 8:
            self.lines.pop(0)

    def update(self, dt_ms: int, energies: Dict[str, float],
               sensitivity: float, flash_thresh: float):
        """
        Update internal state. We store the last audio snapshot so paint() can
        use it to modulate brightness and subtle motion.
        """
        # store last audio state
        self.last_energies = {
            "low": max(0.0, min(1.0, energies.get("low", 0.0))),
            "mid": max(0.0, min(1.0, energies.get("mid", 0.0))),
            "high": max(0.0, min(1.0, energies.get("high", 0.0))),
        }
        self.last_sensitivity = max(0.0, min(1.0, sensitivity))

        # After the beat frame, reset thickness
        if self.beat_flash:
            self.beat_flash = False
        else:
            self.current_line_width = self.base_line_width

        # Optionally, remove the oldest line slowly if energies are very low to keep visuals dynamic
        if self.last_energies["low"] < 0.02 and self.last_energies["mid"] < 0.02:
            # small chance to decay a line
            if random.random() < 0.005:
                if self.lines:
                    self.lines.pop(0)

    def paint(self, painter: QPainter, brightness: float):
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)

        # Compute a pulsing alpha based on mid energy and sensitivity
        mid = self.last_energies.get("mid", 0.0)
        low = self.last_energies.get("low", 0.0)
        high = self.last_energies.get("high", 0.0)
        sens = self.last_sensitivity

        # base alpha scaled by brightness and mid energy (pulsing)
        pulse = 0.5 + 0.5 * mid * sens  # 0.5..1.0
        global_alpha = max(0.0, min(1.0, brightness * pulse))

        # subtle wobble offset from low energy (gives a sense of depth/motion)
        wobble_strength = low * sens * 2.0  # pixels

        for (x1, y1, x2, y2, color) in self.lines:
            # apply tiny wobble to endpoints
            wx1 = x1 + (random.uniform(-1, 1) * wobble_strength)
            wy1 = y1 + (random.uniform(-1, 1) * wobble_strength)
            wx2 = x2 + (random.uniform(-1, 1) * wobble_strength)
            wy2 = y2 + (random.uniform(-1, 1) * wobble_strength)

            c = QColor(color)
            # increase saturation/brightness slightly with high energy
            # convert to HSV-like effect by scaling RGB towards white based on high energy
            hv = max(0.0, min(1.0, high * sens))
            # blend color towards white a bit
            blended_r = int(c.red() + (255 - c.red()) * (hv * 0.25))
            blended_g = int(c.green() + (255 - c.green()) * (hv * 0.25))
            blended_b = int(c.blue() + (255 - c.blue()) * (hv * 0.25))
            c = QColor(blended_r, blended_g, blended_b)
            c.setAlphaF(global_alpha)

            pen = QPen(c, self.current_line_width)
            pen.setCapStyle(Qt.RoundCap)
            pen.setJoinStyle(Qt.RoundJoin)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)

            painter.drawLine(wx1, wy1, wx2, wy2)

            # draw white discs at endpoints
            disc_color = QColor(255, 255, 255)
            # endpoint alpha slightly stronger than line for crispness
            disc_alpha = max(0.0, min(1.0, brightness * (0.8 + 0.2 * mid * sens)))
            disc_color.setAlphaF(disc_alpha)
            painter.setBrush(QBrush(disc_color))
            painter.setPen(Qt.NoPen)

            r = self.endpoint_radius
            painter.drawEllipse(QPointF(wx1, wy1), r, r)
            painter.drawEllipse(QPointF(wx2, wy2), r, r)

        painter.restore()
