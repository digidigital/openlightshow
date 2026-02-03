import math
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QPainter, QColor, QPen
from ..effect_base import Effect


class clapOmaticFast(Effect):
    """Faster variant of clapOmatic that skips hold phases and cycles quickly.

    Phase sequence (each phase lasts one beat interval):
      0 = vertical moving in (left/right -> center)
      1 = rotation center: vertical -> horizontal (smooth)
      2 = horizontal moving out (center -> top & bottom)
      3 = rotation back: horizontal -> vertical (inward swivel, Option B)
      -> repeat
    """

    name: str = "Clap-O-Matic (fast)"
    effect_class: str = "centereffect_class05"

    def __init__(self, size: QSize):
        super().__init__(size)
        self.size = size

        # Geometry
        self.line_width = 5
        self.disc_diameter = 10
        self.num_discs = 12

        # Timing
        self.time_ms = 0.0
        self.last_beat_time_ms = -1000.0
        self.beat_interval_ms = 400.0  # faster default for "fast" mode
        self.beat_debounce_ms = 350.0  # increased debounce as requested

        # 4-phase fast cycle
        self.phase = 0
        self.phase_progress = 0.0

        # Color / audio reactive
        self.hue = 0.0
        self.last_color_change_ms = 0.0
        self.color_change_cooldown_ms = 60.0

        # Glow and flash
        self.glow_strength = 0.0
        self.flash_factor = 1.0

    def resize(self, size: QSize):
        super().resize(size)
        self.size = size

    def _clamp01(self, v: float) -> float:
        return max(0.0, min(1.0, float(v)))

    def _polar(self, vx: float, vy: float):
        r = math.hypot(vx, vy)
        a = math.atan2(vy, vx)
        return r, a

    def _angle_delta_shortest(self, a_from: float, a_to: float) -> float:
        delta = (a_to - a_from) % (2 * math.pi)
        if delta > math.pi:
            delta -= 2 * math.pi
        return delta

    def _interpolate_point_around_pivot(self, px: float, py: float,
                                        sx: float, sy: float,
                                        ex: float, ey: float,
                                        t: float):
        """Interpolate a point from start (sx,sy) to end (ex,ey) around pivot (px,py)
        using polar interpolation (shortest angle + linear radius)."""
        vsx = sx - px
        vsy = sy - py
        rs, as_ = self._polar(vsx, vsy)

        vex = ex - px
        vey = ey - py
        re, ae = self._polar(vex, vey)

        delta = self._angle_delta_shortest(as_, ae)
        a = as_ + delta * t
        r = (1.0 - t) * rs + t * re

        fx = px + r * math.cos(a)
        fy = py + r * math.sin(a)
        return fx, fy

    def update(self, dt_ms: int, energies: dict, sensitivity: float, flash_thresh: float):
        if dt_ms < 0:
            dt_ms = 0
        self.time_ms += dt_ms

        # Progress through current phase (normalized 0..1)
        interval = max(self.beat_interval_ms, 80.0)
        self.phase_progress = min(1.0, self.phase_progress + dt_ms / interval)

        # Audio inputs
        mid = self._clamp01(energies.get("mid", 0.0))
        low = self._clamp01(energies.get("low", 0.0))
        high = self._clamp01(energies.get("high", 0.0))
        sensitivity = self._clamp01(sensitivity)
        flash_thresh = self._clamp01(flash_thresh)

        # Change neon hue on mids
        if mid * sensitivity > 0.55:
            if (self.time_ms - self.last_color_change_ms) > self.color_change_cooldown_ms:
                self.hue = (self.hue + 0.12) % 1.0
                self.last_color_change_ms = self.time_ms

        # Glow from highs (spike + decay)
        self.glow_strength *= 0.88
        if high * sensitivity > 0.45:
            self.glow_strength += 0.35 * high * sensitivity
        self.glow_strength = self._clamp01(self.glow_strength)

        # Flash from overall energy
        overall = max(low, mid, high)
        if overall > flash_thresh:
            self.flash_factor = 1.0 + 0.9 * (overall - flash_thresh)
        else:
            self.flash_factor = 1.0

    def _compute_lines(self):
        """Compute line segments for the fast 4-phase cycle."""
        w = max(1, self.size.width())
        h = max(1, self.size.height())
        lw = float(self.line_width)
        p = self._clamp01(self.phase_progress)

        cx = w * 0.5
        cy = h * 0.5

        lines = []

        # Phase 0: vertical moving in (left/right -> center)
        if self.phase == 0:
            x_left = (1.0 - p) * 0.0 + p * (cx - lw / 2.0)
            x_right = (1.0 - p) * (w - lw) + p * (cx - lw / 2.0)
            lines.append((x_left, 0.0, x_left, float(h)))
            lines.append((x_right, 0.0, x_right, float(h)))

        # Phase 1: rotation center: vertical -> horizontal (smooth)
        elif self.phase == 1:
            # Start: vertical center endpoints
            sx_top_x, sx_top_y = cx, 0.0
            sx_bot_x, sx_bot_y = cx, float(h)
            # End: horizontal center endpoints
            ex_left_x, ex_left_y = 0.0, cy
            ex_right_x, ex_right_y = float(w), cy

            # Interpolate top endpoint -> left endpoint around center pivot
            tx1, ty1 = self._interpolate_point_around_pivot(
                cx, cy,
                sx_top_x, sx_top_y,
                ex_left_x, ex_left_y,
                p
            )
            # Interpolate bottom endpoint -> right endpoint around center pivot
            tx2, ty2 = self._interpolate_point_around_pivot(
                cx, cy,
                sx_bot_x, sx_bot_y,
                ex_right_x, ex_right_y,
                p
            )

            lines.append((tx1, ty1, tx2, ty2))

        # Phase 2: horizontal moving out (center -> top & bottom)
        elif self.phase == 2:
            y_top = (1.0 - p) * (cy - lw / 2.0) + p * 0.0
            y_bottom = (1.0 - p) * (cy - lw / 2.0) + p * (h - lw)
            lines.append((0.0, y_top, float(w), y_top))
            lines.append((0.0, y_bottom, float(w), y_bottom))

        # Phase 3: rotation back horizontal -> vertical (inward swivel, Option B)
        elif self.phase == 3:
            # Top line rotates around top-left pivot (0,0) -> ends as left vertical (0,0)->(0,h)
            pivot_top_x, pivot_top_y = 0.0, 0.0
            sx1_tx, sx1_ty = 0.0, 0.0
            sx2_tx, sx2_ty = float(w), 0.0
            ex1_tx, ex1_ty = 0.0, 0.0
            ex2_tx, ex2_ty = 0.0, float(h)

            top_a_x, top_a_y = self._interpolate_point_around_pivot(
                pivot_top_x, pivot_top_y,
                sx1_tx, sx1_ty,
                ex1_tx, ex1_ty,
                p
            )
            top_b_x, top_b_y = self._interpolate_point_around_pivot(
                pivot_top_x, pivot_top_y,
                sx2_tx, sx2_ty,
                ex2_tx, ex2_ty,
                p
            )

            # Bottom line rotates around bottom-left pivot (0,h) -> ends as right vertical (w,0)->(w,h)
            pivot_bot_x, pivot_bot_y = 0.0, float(h)
            sx1_bx, sx1_by = 0.0, float(h)
            sx2_bx, sx2_by = float(w), float(h)
            ex1_bx, ex1_by = float(w), 0.0
            ex2_bx, ex2_by = float(w), float(h)

            bot_a_x, bot_a_y = self._interpolate_point_around_pivot(
                pivot_bot_x, pivot_bot_y,
                sx1_bx, sx1_by,
                ex1_bx, ex1_by,
                p
            )
            bot_b_x, bot_b_y = self._interpolate_point_around_pivot(
                pivot_bot_x, pivot_bot_y,
                sx2_bx, sx2_by,
                ex2_bx, ex2_by,
                p
            )

            lines.append((top_a_x, top_a_y, top_b_x, top_b_y))
            lines.append((bot_a_x, bot_a_y, bot_b_x, bot_b_y))

        return lines

    def _draw_discs(self, painter: QPainter, x1: float, y1: float, x2: float, y2: float, count: int):
        d = float(self.disc_diameter)
        if count <= 0:
            return
        for i in range(count):
            t = float(i + 1) / float(count + 1)
            px = x1 + (x2 - x1) * t
            py = y1 + (y2 - y1) * t
            painter.drawEllipse(px - d / 2.0, py - d / 2.0, d, d)

    def paint(self, painter: QPainter, brightness: float):
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)

        # Clamp brightness
        brightness = max(0.1, min(float(brightness), 2.0))

        # Glow multiplier (clamped)
        glow = 1.0 + 1.6 * self.glow_strength
        glow = max(0.0, min(glow, 3.0))

        # Neon color reacts to hue and flash
        val = self._clamp01(0.85 * brightness * self.flash_factor * glow)
        color = QColor.fromHsvF(self.hue, 1.0, val)

        pen = QPen(color)
        pen.setWidth(self.line_width)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)

        lines = self._compute_lines()

        # Draw lines
        for x1, y1, x2, y2 in lines:
            painter.drawLine(int(round(x1)), int(round(y1)), int(round(x2)), int(round(y2)))

        # Draw discs (white) evenly distributed along each line
        painter.setPen(Qt.NoPen)
        disc_color = QColor(255, 255, 255)
        alpha_float = 255.0 * brightness * glow
        alpha_int = int(max(0.0, min(alpha_float, 255.0)))
        disc_color.setAlpha(alpha_int)
        painter.setBrush(disc_color)

        if len(lines) == 0:
            pass
        elif len(lines) == 1:
            x1, y1, x2, y2 = lines[0]
            self._draw_discs(painter, x1, y1, x2, y2, self.num_discs)
        else:
            per_line = max(1, self.num_discs // len(lines))
            for x1, y1, x2, y2 in lines:
                self._draw_discs(painter, x1, y1, x2, y2, per_line)

        painter.restore()

    def on_beat(self):
        now = self.time_ms
        # stronger debounce: ignore beats that arrive sooner than beat_debounce_ms
        if now - self.last_beat_time_ms < self.beat_debounce_ms:
            return

        if self.last_beat_time_ms > 0.0:
            interval = now - self.last_beat_time_ms
            # Smoothly adapt beat interval but keep it fast
            self.beat_interval_ms = 0.75 * self.beat_interval_ms + 0.25 * max(interval, 80.0)

        self.last_beat_time_ms = now

        # Advance phase in 4-phase fast cycle
        self.phase = (self.phase + 1) % 4
        self.phase_progress = 0.0

        super().on_beat()

