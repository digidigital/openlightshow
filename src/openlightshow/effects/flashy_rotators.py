import math
import random
import time
from typing import Dict, List, Tuple

from PySide6.QtCore import Qt, QSize, QPointF, QRectF
from PySide6.QtGui import QPainter, QColor, QPen, QBrush

from ..effect_base import Effect


class FlashyRotators(Effect):
    """
    FlashyRotators with stronger debounce, deferred initialization, and single-frame clear.

    - Exactly `count` rotating arms.
    - Rotators are initialized only after a valid resize() or on the first accepted beat.
    - On beat: respawn all arms only if debounce period has passed.
    - Single-frame clear on the next paint after respawn to remove host artifacts.
    """

    name = "FlashyRotators"
    effect_class = "centereffect_class07"

    def __init__(self, size: QSize):
        super().__init__(size)
        # store size but defer placement until resize() or first beat
        self.size = size

        self.rotators: List[Dict] = []
        self.count = 5
        self.base_line_width = 5
        self.current_line_width = self.base_line_width
        self.endpoint_radius = 3.0

        # ensure beat_flash exists to avoid AttributeError
        self.beat_flash = False

        # audio snapshot
        self.last_energies: Dict[str, float] = {"low": 0.0, "mid": 0.0, "high": 0.0}
        self.last_sensitivity: float = 0.5

        self.neon_colors = [
            QColor(57, 255, 20),
            QColor(199, 21, 133),
            QColor(255, 20, 147),
            QColor(255, 255, 0),
            QColor(255, 165, 0),
            QColor(0, 255, 255),
            QColor(255, 0, 255),
        ]

        # debounce / timing
        self.debounce_ms = 400  # minimum ms between respawns
        self._last_beat_ts = 0.0  # monotonic time in seconds

        # single-frame clear flag (set when we respawn; paint will clear once)
        self.clear_next_frame = False

        # generation counter for debugging / determinism
        self.generation = 0

        # defer initialization until resize() or first accepted beat
        self._needs_init = True

    # ---------------- geometry helpers ----------------
    def _segments_intersect(self, a1, a2, b1, b2) -> bool:
        (x1, y1), (x2, y2) = a1, a2
        (x3, y3), (x4, y4) = b1, b2

        def orient(ax, ay, bx, by, cx, cy):
            return (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)

        def on_segment(ax, ay, bx, by, cx, cy):
            return min(ax, bx) <= cx <= max(ax, bx) and min(ay, by) <= cy <= max(ay, by)

        o1 = orient(x1, y1, x2, y2, x3, y3)
        o2 = orient(x1, y1, x2, y2, x4, y4)
        o3 = orient(x3, y3, x4, y4, x1, y1)
        o4 = orient(x3, y3, x4, y4, x2, y2)

        if (o1 > 0 and o2 < 0 or o1 < 0 and o2 > 0) and (o3 > 0 and o4 < 0 or o3 < 0 and o4 > 0):
            return True

        if o1 == 0 and on_segment(x1, y1, x2, y2, x3, y3):
            return True
        if o2 == 0 and on_segment(x1, y1, x2, y2, x4, y4):
            return True
        if o3 == 0 and on_segment(x3, y3, x4, y4, x1, y1):
            return True
        if o4 == 0 and on_segment(x3, y3, x4, y4, x2, y2):
            return True

        return False

    def _arm_endpoint(self, sx: float, sy: float, length: float, angle: float) -> Tuple[float, float]:
        return sx + math.cos(angle) * length, sy + math.sin(angle) * length

    # ---------------- placement ----------------
    def _init_rotators(self):
        """Reset and create exactly self.count rotators with best-effort non-intersection across full rotation."""
        self.rotators = []
        w = max(1, self.size.width())
        h = max(1, self.size.height())
        length = h / 5.0
        margin = length + 1.0

        attempts_limit = 1200
        samples = 24
        tries = 0

        while len(self.rotators) < self.count and tries < attempts_limit:
            tries += 1
            sx = random.uniform(margin, w - margin)
            sy = random.uniform(margin, h - margin)
            base_angle = random.uniform(0, 2 * math.pi)
            ang_vel = random.uniform(0.008, 0.02)
            if random.random() < 0.5:
                ang_vel = -ang_vel
            color = random.choice(self.neon_colors)

            sampled_new = []
            valid = True
            for s in range(samples):
                a = base_angle + (2 * math.pi * s / samples)
                ex, ey = self._arm_endpoint(sx, sy, length, a)
                sampled_new.append(((sx, sy), (ex, ey)))
                if not (0 <= ex <= w and 0 <= ey <= h):
                    valid = False
                    break
            if not valid:
                continue

            for existing in self.rotators:
                esx, esy = existing["start"]
                elen = existing["length"]
                ebase = existing["angle"]
                for s in range(samples):
                    ea = ebase + (2 * math.pi * s / samples)
                    eex, eey = self._arm_endpoint(esx, esy, elen, ea)
                    for (a1, a2) in sampled_new:
                        if self._segments_intersect(a1, a2, (esx, esy), (eex, eey)):
                            valid = False
                            break
                    if not valid:
                        break
                if not valid:
                    break

            if not valid:
                continue

            self.rotators.append({
                "start": (sx, sy),
                "length": length,
                "angle": base_angle,
                "ang_vel": ang_vel,
                "color": color,
            })

        # fallback conservative placement if needed
        if len(self.rotators) < self.count:
            center_x = w / 2.0
            center_y = h / 2.0
            radius = max(0, min(w, h) / 4.0)
            for i in range(len(self.rotators), self.count):
                theta = (2 * math.pi * i) / self.count
                sx = center_x + math.cos(theta) * radius
                sy = center_y + math.sin(theta) * radius
                sx = min(max(margin, sx), w - margin)
                sy = min(max(margin, sy), h - margin)
                self.rotators.append({
                    "start": (sx, sy),
                    "length": length,
                    "angle": random.uniform(0, 2 * math.pi),
                    "ang_vel": random.choice([0.01, -0.01]),
                    "color": random.choice(self.neon_colors),
                })

        # mark that initialization has been performed
        self._needs_init = False

    # ---------------- resize ----------------
    def resize(self, size: QSize):
        super().resize(size)
        self.size = size
        # Reinitialize rotators to cover the new canvas fully
        self._init_rotators()

    # ---------------- beat handling with debounce ----------------
    def on_beat(self):
        super().on_beat()
        now = time.monotonic()
        elapsed_ms = (now - self._last_beat_ts) * 1000.0
        if elapsed_ms < self.debounce_ms:
            # ignore this beat — still in debounce window
            return

        # ensure rotators are initialized with current size before respawn
        if self._needs_init or not self.rotators:
            self._init_rotators()

        # accept beat: respawn rotators and schedule a single-frame clear
        self._last_beat_ts = now
        self.generation += 1
        self.beat_flash = True
        self.current_line_width = self.base_line_width + 2

        # respawn rotators at new positions (guaranteed non-intersecting best-effort)
        self._init_rotators()

        # mark that paint should clear once on next frame to remove host artifacts
        self.clear_next_frame = True

        # small color/phase nudge for variety
        for rot in self.rotators:
            if random.random() < 0.5:
                rot["color"] = random.choice(self.neon_colors)
            rot["angle"] += random.uniform(-0.3, 0.3)

    # ---------------- update ----------------
    def update(self, dt_ms: int, energies: Dict[str, float],
               sensitivity: float, flash_thresh: float):
        self.last_energies = {
            "low": max(0.0, min(1.0, energies.get("low", 0.0))),
            "mid": max(0.0, min(1.0, energies.get("mid", 0.0))),
            "high": max(0.0, min(1.0, energies.get("high", 0.0))),
        }
        self.last_sensitivity = max(0.0, min(1.0, sensitivity))

        for rot in self.rotators:
            hv = self.last_energies["high"] * self.last_sensitivity * 0.6
            ang_step = rot["ang_vel"] * (1.0 + hv) * dt_ms
            rot["angle"] = (rot["angle"] + ang_step) % (2 * math.pi)

        # reset beat flash after update so paint sees it only when appropriate
        if self.beat_flash:
            # keep beat_flash True until paint runs once (paint will clear and then we reset)
            pass
        else:
            self.current_line_width = self.base_line_width

    # ---------------- paint ----------------
    def paint(self, painter: QPainter, brightness: float):
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)

        # If initialization hasn't happened yet (no valid size), do it now
        if self._needs_init:
            # attempt to initialize with current stored size
            self._init_rotators()

        # If we flagged a clear for the next frame, do a single-frame clear now and reset the flag.
        if self.clear_next_frame:
            try:
                painter.save()
                painter.setCompositionMode(QPainter.CompositionMode_Source)
                painter.fillRect(QRectF(0, 0, self.size.width(), self.size.height()), QColor(0, 0, 0, 0))
                painter.restore()
            except Exception:
                # if composition mode unsupported, ignore but continue (no crash)
                pass
            # ensure we only clear once
            self.clear_next_frame = False
            # keep beat_flash True for this paint so the boosted width is visible this frame

        mid = self.last_energies.get("mid", 0.0)
        low = self.last_energies.get("low", 0.0)
        high = self.last_energies.get("high", 0.0)
        sens = self.last_sensitivity

        pulse = 0.6 + 0.4 * mid * sens
        global_alpha = max(0.0, min(1.0, brightness * pulse))
        wobble_strength = low * sens * 1.5

        # draw exactly self.count arms (no other geometry)
        for rot in self.rotators:
            sx, sy = rot["start"]
            length = rot["length"]
            angle = rot["angle"]

            ex = sx + math.cos(angle) * length + random.uniform(-1, 1) * wobble_strength
            ey = sy + math.sin(angle) * length + random.uniform(-1, 1) * wobble_strength

            c = QColor(rot["color"])
            hv = max(0.0, min(1.0, high * sens))
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

            painter.drawLine(sx, sy, ex, ey)

            disc_color = QColor(255, 255, 255)
            disc_alpha = max(0.0, min(1.0, brightness * (0.85 + 0.15 * mid * sens)))
            disc_color.setAlphaF(disc_alpha)
            painter.setBrush(QBrush(disc_color))
            painter.setPen(Qt.NoPen)

            r = self.endpoint_radius
            painter.drawEllipse(QPointF(sx, sy), r, r)
            painter.drawEllipse(QPointF(ex, ey), r, r)

        # after painting the beat frame, clear beat_flash so update() can reset width next tick
        if self.beat_flash:
            self.beat_flash = False

        painter.restore()
