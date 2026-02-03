# src/openlightshow/effects/laser_fan_path.py
from PySide6.QtCore import QSize, QPointF, Qt
from PySide6.QtGui import QPainter, QColor, QBrush
from ..effect_base import Effect
import math
import time


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def ease_out_cubic(t: float) -> float:
    t = clamp(t, 0.0, 1.0)
    return 1 - pow(1 - t, 3)


class LaserFanPath(Effect):
    """
    LaserFanPath:
    - 12 neon discs (20px) that cycle through a sequence of formations on each beat:
      0: top spread
      1: diagonal top-left -> bottom-right
      2: right vertical
      3: diagonal bottom-left -> top-right
      4: bottom spread
      5: diagonal top-left -> bottom-right
      6: left vertical
      7: diagonal bottom-left -> top-right
      then back to 0
    - On each beat the formation advances. Transitions are constrained so that ALL discs
      move along a single axis only (either purely horizontal OR purely vertical).
      The axis is chosen automatically per-transition by comparing total required movement
      along X and Y and picking the larger one. This prevents any per-disc diagonal motion.
    - Colors shift to bright neon hues driven by energies['mid'].
    """

    name: str = "LaserFanPath"
    effect_class: str = "particle_class01"

    def __init__(self, size: QSize):
        super().__init__(size)
        self.size = size

        # Visual layout
        self.count = 12
        self.diameter = 20.0
        self.radius = self.diameter / 2.0
        self.margin = 10.0

        # positions
        self.start_positions = []   # positions at start of current animation
        self.current_positions = [] # current positions (kept in sync)
        self.target_positions = []  # target formation positions (after axis constraint)

        # formation sequencing
        self.formation_index = 0
        self.formations_count = 8

        # animation timing
        self.movement_progress = 1.0  # 0..1
        self.move_duration_ms = 260.0
        self.last_beat_time = 0.0
        self.beat_debounce_ms = 200.0

        # audio state
        self.last_low = 0.0
        self.last_mid = 0.0
        self.last_high = 0.0

        # color base
        self.base_hue = 0.58
        self.saturation = 0.95
        self.base_val = 0.95

        # initialize formations and positions
        self._recalc_formations(initial=True)

    def _linspace(self, a: float, b: float, n: int):
        if n == 1:
            return [(a + b) / 2.0]
        step = (b - a) / (n - 1)
        return [a + i * step for i in range(n)]

    def _recalc_formations(self, initial: bool = False):
        """Compute formation target positions for the current canvas size."""
        w = max(1.0, float(self.size.width()))
        h = max(1.0, float(self.size.height()))

        left_x = self.margin + self.radius
        right_x = w - self.margin - self.radius
        top_y = self.margin + self.radius
        bottom_y = h - self.margin - self.radius
        center_x = w / 2.0
        center_y = h / 2.0

        # Formation 0: top spread (evenly across width at top_y)
        xs_top = self._linspace(self.margin + self.radius, w - self.margin - self.radius, self.count)
        f_top = [QPointF(x, top_y) for x in xs_top]

        # Formation 1: diagonal top-left -> bottom-right
        xs_d1 = self._linspace(left_x, right_x, self.count)
        ys_d1 = self._linspace(top_y, bottom_y, self.count)
        f_diag_tl_br = [QPointF(xs_d1[i], ys_d1[i]) for i in range(self.count)]

        # Formation 2: right vertical (evenly spaced along right_x)
        ys_right = self._linspace(top_y, bottom_y, self.count)
        f_right = [QPointF(right_x, y) for y in ys_right]

        # Formation 3: diagonal bottom-left -> top-right
        xs_d2 = self._linspace(left_x, right_x, self.count)
        ys_d2 = self._linspace(bottom_y, top_y, self.count)
        f_diag_bl_tr = [QPointF(xs_d2[i], ys_d2[i]) for i in range(self.count)]

        # Formation 4: bottom spread
        xs_bottom = self._linspace(self.margin + self.radius, w - self.margin - self.radius, self.count)
        f_bottom = [QPointF(x, bottom_y) for x in xs_bottom]

        # Formation 5: diagonal top-left -> bottom-right (repeat)
        f_diag_tl_br_2 = f_diag_tl_br

        # Formation 6: left vertical
        ys_left = self._linspace(top_y, bottom_y, self.count)
        f_left = [QPointF(left_x, y) for y in ys_left]

        # Formation 7: diagonal bottom-left -> top-right (repeat)
        f_diag_bl_tr_2 = f_diag_bl_tr

        self._formations = [
            f_top,            # 0 top
            f_diag_tl_br,     # 1 diagonal TL->BR
            f_right,          # 2 right
            f_diag_bl_tr,     # 3 diagonal BL->TR
            f_bottom,         # 4 bottom
            f_diag_tl_br_2,   # 5 diagonal TL->BR
            f_left,           # 6 left
            f_diag_bl_tr_2,   # 7 diagonal BL->TR
        ]

        # ensure formation_index is valid
        self.formation_index %= self.formations_count

        # set target to current formation index
        self.target_positions = [QPointF(p.x(), p.y()) for p in self._formations[self.formation_index]]

        # initialize current/start positions on first run
        if initial or not self.current_positions:
            self.current_positions = [QPointF(p.x(), p.y()) for p in self.target_positions]
            self.start_positions = [QPointF(p.x(), p.y()) for p in self.target_positions]

    def resize(self, size: QSize):
        super().resize(size)
        self.size = size
        # recalc formations and snap current positions to the nearest new formation positions
        self._recalc_formations(initial=True)

    def _reorder_by_axis(self, start_list, target_list, axis: str):
        """
        Reorder target_list so that mapping from start_list -> target_list preserves ordering
        along the given axis ('x' or 'y'). This prevents crossing when all discs move along
        the other axis.
        """
        if not start_list or not target_list or len(start_list) != len(target_list):
            return [QPointF(p.x(), p.y()) for p in target_list]

        if axis == 'y':
            # preserve start y-ordering, map to targets sorted by y
            start_order = sorted(range(len(start_list)), key=lambda i: start_list[i].y())
            targets_sorted = sorted(target_list, key=lambda p: p.y())
        else:
            # axis == 'x'
            start_order = sorted(range(len(start_list)), key=lambda i: start_list[i].x())
            targets_sorted = sorted(target_list, key=lambda p: p.x())

        reordered = [None] * len(target_list)
        for idx, start_idx in enumerate(start_order):
            reordered[start_idx] = QPointF(targets_sorted[idx].x(), targets_sorted[idx].y())

        for i in range(len(reordered)):
            if reordered[i] is None:
                reordered[i] = QPointF(target_list[i].x(), target_list[i].y())

        return reordered

    def update(self, dt_ms: int, energies: dict,
               sensitivity: float, flash_thresh: float):
        """
        energies: {'low': 0.0-1.0, 'mid': 0.0-1.0, 'high': 0.0-1.0}
        sensitivity: 0.0-1.0
        flash_thresh: 0.0-1.0
        """
        low = clamp(float(energies.get('low', 0.0)), 0.0, 1.0)
        mid = clamp(float(energies.get('mid', 0.0)), 0.0, 1.0)
        high = clamp(float(energies.get('high', 0.0)), 0.0, 1.0)
        sensitivity = clamp(float(sensitivity), 0.0, 1.0)
        flash_thresh = clamp(float(flash_thresh), 0.0, 1.0)

        self.last_low = low
        self.last_mid = mid
        self.last_high = high

        # progress animation
        if self.movement_progress < 1.0:
            self.movement_progress += (dt_ms / max(1.0, self.move_duration_ms))
            if self.movement_progress >= 1.0:
                self.movement_progress = 1.0
                # finalize positions
                self.current_positions = [QPointF(p.x(), p.y()) for p in self.target_positions]
                self.start_positions = [QPointF(p.x(), p.y()) for p in self.target_positions]

        # hue modulation driven by mid energy
        hue_shift = (self.last_mid * sensitivity) * 0.18  # up to +/-0.18
        phase = math.sin(time.time() * 0.9)
        self.current_hue = clamp(self.base_hue + hue_shift * phase, 0.0, 1.0)

    def paint(self, painter: QPainter, brightness: float):
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)

        brightness = clamp(float(brightness), 0.1, 2.0)
        t_raw = clamp(self.movement_progress, 0.0, 1.0)
        t = ease_out_cubic(t_raw)

        # Interpolate positions strictly along the chosen axis:
        # start -> target already constrained so interpolation is linear and axis-only.
        for i in range(self.count):
            start = self.start_positions[i]
            target = self.target_positions[i]

            ix = start.x() + (target.x() - start.x()) * t
            iy = start.y() + (target.y() - start.y()) * t

            # color: hue varies across dots slightly and with mid energy
            phase = (i / max(1, self.count - 1))
            per_dot_offset = (phase - 0.5) * 0.06
            hue = clamp(self.current_hue + per_dot_offset, 0.0, 1.0)

            # value modulated by mid and high for punch
            v = clamp(self.base_val * (0.75 + 0.25 * self.last_mid) * brightness, 0.0, 1.0)
            shimmer = 0.03 * math.sin(time.time() * 22.0 + i * 0.9)
            v = clamp(v + shimmer * self.last_high, 0.0, 1.0)

            color = QColor.fromHsvF(hue, self.saturation, v)
            painter.setBrush(QBrush(color))

            painter.drawEllipse(QPointF(ix - self.radius, iy - self.radius),
                                self.radius, self.radius)

        painter.restore()

    def on_beat(self):
        """
        Advance to the next formation on each accepted beat.
        For the transition we:
          - compute raw new targets for the new formation
          - decide whether the transition should be horizontal-only or vertical-only
            by summing absolute deltas across all discs and picking the larger axis
          - reorder targets to match start ordering along the axis that will remain fixed
            (prevents crossing during the moving axis)
          - constrain targets so only the chosen axis changes
          - start animation
        """
        now_ms = time.time() * 1000.0
        if (now_ms - self.last_beat_time) < self.beat_debounce_ms:
            return

        self.last_beat_time = now_ms

        # advance formation index
        self.formation_index = (self.formation_index + 1) % self.formations_count

        # raw new targets for the new formation
        raw_targets = [QPointF(p.x(), p.y()) for p in self._formations[self.formation_index]]

        # ensure current_positions length
        if len(self.current_positions) != self.count:
            # fallback: initialize current positions to current targets to avoid errors
            self.current_positions = [QPointF(p.x(), p.y()) for p in raw_targets]

        # compute total absolute delta along each axis
        total_dx = 0.0
        total_dy = 0.0
        for i in range(self.count):
            sx = self.current_positions[i].x()
            sy = self.current_positions[i].y()
            tx = raw_targets[i].x()
            ty = raw_targets[i].y()
            total_dx += abs(tx - sx)
            total_dy += abs(ty - sy)

        # choose axis with larger total movement; if equal prefer horizontal
        if total_dx >= total_dy:
            chosen_axis = 'x'  # animate horizontally only (x changes, y stays)
            # reorder raw_targets to match start y-order so horizontal moves don't cross
            reordered = self._reorder_by_axis(self.current_positions, raw_targets, axis='y')
            # constrain targets: keep y from start, x from reordered target
            constrained = [QPointF(reordered[i].x(), self.current_positions[i].y()) for i in range(self.count)]
        else:
            chosen_axis = 'y'  # animate vertically only (y changes, x stays)
            # reorder raw_targets to match start x-order so vertical moves don't cross
            reordered = self._reorder_by_axis(self.current_positions, raw_targets, axis='x')
            # constrain targets: keep x from start, y from reordered target
            constrained = [QPointF(self.current_positions[i].x(), reordered[i].y()) for i in range(self.count)]

        # set start and target positions for the animation
        self.start_positions = [QPointF(p.x(), p.y()) for p in self.current_positions]
        self.target_positions = constrained

        # start animation
        self.movement_progress = 0.0

        super().on_beat()
