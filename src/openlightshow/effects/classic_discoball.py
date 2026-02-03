from random import uniform, random, randint
from time import time

from PySide6.QtCore import QSize
from PySide6.QtGui import QPainter, QColor
from ..effect_base import Effect


def _clamp01(v: float) -> float:
    if v < 0.0:
        return 0.0
    if v > 1.0:
        return 1.0
    return v


class ClasssicDiscoball(Effect):
    """
    ClassicDiscoball effect.
    - 50 x 20 px "mirror" tiles arranged in horizontal lanes.
    - Tiles in each lane are spaced 200 px apart horizontally.
    - Lanes are spaced 150 px vertically.
    - Each lane has a random horizontal offset so tiles don't line up vertically.
    - All lanes move in the same global horizontal direction (either all left or all right).
    - Base speed is 10x the original base; each lane's speed varies ±25%.
    - On detected beat, all tiles switch to a neon color (same color for all tiles) briefly.
    - Reacts to audio energies: low/mid/high influence brightness and movement responsiveness.
    """

    name: str = "ClassicDiscoball"
    effect_class: str = "particle_class01"

    TILE_W = 50
    TILE_H = 20
    TILE_SPACING_X = 200
    LANE_SPACING_Y = 150
    # base speed for lanes (px per second) multiplied by 2.0 as requested
    DEFAULT_SPEED_PX_PER_S = 80.0 * 10.0
    BEAT_COOLDOWN_MS = 150

    def __init__(self, size: QSize):
        super().__init__(size)
        self.size = size
        self.width = max(1, size.width())
        self.height = max(1, size.height())

        # global direction for all lanes: 1 (right) or -1 (left), 50% chance each
        self.global_direction = 1 if random() < 0.5 else -1

        # lanes: list of dicts { y, speed_factor, offset }
        # offset is continuously updated; tiles are generated each paint call to avoid gaps
        self.lanes = []
        self._init_lanes()

        # neon color state (h in 0..1)
        self.current_hue = uniform(0.0, 1.0)
        self.neon_saturation = 0.95
        self.neon_value = 1.0

        # flash / beat state
        self._last_beat_time = 0.0
        self._flash_progress = 0.0  # 0.0 -> no flash, 1.0 -> full flash
        self._flash_decay_per_ms = 0.0025  # how fast flash fades (tunable)

        # subtle per-frame jitter to avoid perfectly static look
        self._jitter = 0.0

    def _init_lanes(self):
        self.lanes = []
        # compute how many lanes fit vertically
        lane_count = max(1, (self.height + self.LANE_SPACING_Y - 1) // self.LANE_SPACING_Y)
        # center lanes vertically
        total_height = (lane_count - 1) * self.LANE_SPACING_Y
        top = (self.height - total_height) / 2.0

        for i in range(int(lane_count)):
            y = int(top + i * self.LANE_SPACING_Y)
            # speed factor ±25%
            speed_factor = uniform(0.75, 1.25)
            # base offset ensures lanes don't vertically align
            base_offset = uniform(0.0, self.TILE_SPACING_X)
            # dynamic offset updated each frame (float)
            offset = base_offset
            lane = {
                "y": y,
                "speed_factor": speed_factor,
                "base_offset": base_offset,
                "offset": offset,
            }
            self.lanes.append(lane)

    def resize(self, size: QSize):
        super().resize(size)
        self.size = size
        self.width = max(1, size.width())
        self.height = max(1, size.height())
        # preserve global direction on resize
        self._init_lanes()

    def update(self, dt_ms: int, energies: dict,
               sensitivity: float, flash_thresh: float):
        """
        Move lanes, update flash progress and jitter based on audio.
        energies: {'low': 0.0-1.0, 'mid': 0.0-1.0, 'high': 0.0-1.0}
        sensitivity: 0.0-1.0
        flash_thresh: 0.0-1.0
        """
        # clamp energies
        low = _clamp01(float(energies.get("low", 0.0)))
        mid = _clamp01(float(energies.get("mid", 0.0)))
        high = _clamp01(float(energies.get("high", 0.0)))

        # Use low energy to slightly modulate lane speeds (bass pushes movement)
        bass_influence = 1.0 + (low - 0.2) * 0.6 * sensitivity
        # Use mid energy to add jitter to tile positions (rhythmic shimmer)
        self._jitter = mid * 2.0 * sensitivity

        dt_s = max(0.0001, dt_ms / 1000.0)
        for lane in self.lanes:
            # lane speed = base * lane factor * global direction * bass_influence
            lane_speed = self.DEFAULT_SPEED_PX_PER_S * lane["speed_factor"]
            move_px = self.global_direction * lane_speed * bass_influence * dt_s
            # also let high frequencies cause small extra nudges
            move_px += self.global_direction * lane_speed * 0.05 * high * sensitivity * dt_s
            # update lane offset (continuous) to avoid gaps
            lane["offset"] += move_px

            # keep offset bounded to avoid float runaway (modulo spacing)
            lane["offset"] = (lane["offset"] % self.TILE_SPACING_X)

        # Flash decay
        if self._flash_progress > 0.0:
            self._flash_progress -= self._flash_decay_per_ms * dt_ms
            if self._flash_progress < 0.0:
                self._flash_progress = 0.0

        # If energies exceed flash_thresh and sensitivity is high enough, trigger a small flash
        if (mid * sensitivity) > flash_thresh and self._flash_progress < 0.15:
            # small pulse
            self._flash_progress = min(1.0, self._flash_progress + 0.12 * (mid * sensitivity))

    def paint(self, painter: QPainter, brightness: float):
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)

        # clamp brightness
        brightness = max(0.1, min(2.0, float(brightness)))

        # compute neon color (HSV) - same for all tiles
        h = _clamp01(self.current_hue)
        s = _clamp01(self.neon_saturation)
        # value is influenced by flash progress and brightness
        v_base = _clamp01(self.neon_value * brightness)
        v = _clamp01(v_base + self._flash_progress * (1.0 - v_base))

        neon_color = QColor.fromHsvF(h, s, v)
        # a dim "mirror" base color (light gray) for tiles when not neon
        base_gray = QColor(200, 200, 200)

        buffer = self.TILE_SPACING_X * 2

        # draw each lane's tiles by generating positions from offset to cover the screen continuously
        for lane in self.lanes:
            y = int(lane["y"])
            # compute starting x so tiles cover from -buffer to width + buffer
            # offset is in [0, TILE_SPACING_X)
            start_x = -buffer - (lane["offset"])
            # generate tiles across the screen; using spacing ensures no gaps
            x = start_x
            while x < self.width + buffer:
                # apply small jitter to avoid perfectly rigid grid
                jitter_x = uniform(-self._jitter, self._jitter)
                jitter_y = uniform(-self._jitter * 0.5, self._jitter * 0.5)
                rx = int(x + jitter_x)
                ry = int(y + jitter_y)

                # decide tile color: when flash_progress > 0.02 show neon, else base gray
                if self._flash_progress > 0.02:
                    t = _clamp01(self._flash_progress)
                    nr = int(neon_color.red() * t + base_gray.red() * (1.0 - t))
                    ng = int(neon_color.green() * t + base_gray.green() * (1.0 - t))
                    nb = int(neon_color.blue() * t + base_gray.blue() * (1.0 - t))
                    color = QColor(max(0, min(255, nr)),
                                   max(0, min(255, ng)),
                                   max(0, min(255, nb)))
                else:
                    color = base_gray

                # draw the tile rectangle
                painter.setPen(color)
                painter.setBrush(color)
                painter.drawRect(rx, ry - self.TILE_H // 2, self.TILE_W, self.TILE_H)

                # draw a subtle neon rim/glow when neon is active (thin translucent border)
                if self._flash_progress > 0.05:
                    glow_alpha = int(180 * _clamp01(self._flash_progress))
                    rim = QColor(neon_color.red(), neon_color.green(), neon_color.blue(), glow_alpha)
                    painter.setPen(rim)
                    painter.setBrush(rim)
                    # draw a thin ellipse to simulate reflected light in smoke
                    gx = rx + self.TILE_W // 2 - 6
                    gy = ry + self.TILE_H // 2 - 6
                    gw = 12
                    gh = 6
                    painter.drawEllipse(gx, gy, gw, gh)

                x += self.TILE_SPACING_X

        painter.restore()

    def on_beat(self):
        """
        Triggered on detected beats. Change neon hue for all tiles and create a strong flash.
        Debounced by BEAT_COOLDOWN_MS.
        """
        now_ms = int(time() * 1000)
        if now_ms - int(self._last_beat_time * 1000) < self.BEAT_COOLDOWN_MS:
            return
        self._last_beat_time = time()

        # pick a new neon hue (neon palette: vivid hues)
        neon_palettes = [
            (0.0, 0.08),    # red/orange
            (0.08, 0.18),   # orange/yellow
            (0.18, 0.33),   # yellow/green
            (0.33, 0.55),   # green/cyan
            (0.55, 0.75),   # cyan/blue
            (0.75, 0.95),   # purple/magenta
        ]
        palette = neon_palettes[randint(0, len(neon_palettes) - 1)]
        new_hue = uniform(palette[0], palette[1])
        self.current_hue = _clamp01(new_hue)

        # strong flash triggered by beat
        self._flash_progress = 1.0

        # small chance to flip the global direction for variety (keeps all lanes moving same way)
        if uniform(0.0, 1.0) < 0.12:
            self.global_direction = 1 if random() < 0.5 else -1

        super().on_beat()
