import time
import random
import math
from PySide6.QtCore import QSize, QPointF, Qt
from PySide6.QtGui import QPainter, QColor, QPen
from ..effect_base import Effect


class ScreenX(Effect):
    """
    ScreenX Effect:
    - Two 2px wide diagonal lines forming an X from corner to corner
    - Color shifts based on mid-range frequencies
    - On each beat, bright white pulse lines travel from center to corners
    - Pulses are 80px long and 8px wide for high visibility
    - Pulses reach screen corners within one beat
    - 200ms beat debounce
    """

    name = "Screen X"
    effect_class = "centereffect_class01"

    def __init__(self, size: QSize):
        super().__init__(size)

        # Beat debounce
        self.last_beat_time = 0.0
        self.beat_debounce_ms = 200

        # Beat interval tracking for pulse speed
        self.beat_times = []
        self.max_beat_history = 4
        self.measured_beat_interval = 0.5  # Initial guess (120 BPM)

        # Color shifting based on mids
        self.hue_shift = 0.0

        # Neon colors - base colors to shift from
        self.neon_colors = [
            QColor(57, 255, 20),    # neon green
            QColor(255, 20, 147),   # neon pink
            QColor(0, 255, 255),    # neon cyan
            QColor(255, 255, 0),    # neon yellow
            QColor(255, 0, 255),    # neon magenta
            QColor(255, 165, 0),    # neon orange
            QColor(0, 255, 128),    # neon lime
            QColor(255, 50, 255),   # bright purple
        ]

        self.base_color = random.choice(self.neon_colors)

        # Pulses: list of dicts with direction and progress
        self.pulses = []

        # Energy tracking
        self.mid_energy = 0.0

    def on_beat(self):
        # Debounce
        now = time.time()
        if (now - self.last_beat_time) * 1000.0 < self.beat_debounce_ms:
            return

        # Track beat timing
        self.beat_times.append(now)
        if len(self.beat_times) > self.max_beat_history:
            self.beat_times.pop(0)

        # Calculate average beat interval from recent beats
        if len(self.beat_times) >= 2:
            intervals = [self.beat_times[i] - self.beat_times[i-1]
                        for i in range(1, len(self.beat_times))]
            self.measured_beat_interval = sum(intervals) / len(intervals)

        self.last_beat_time = now

        super().on_beat()

        # Always create pulses on beat (don't wait for beat measurement)
        # Create 4 pulses, one for each direction of the X
        # Directions: 0=top-left corner, 1=top-right corner
        #             2=bottom-right corner, 3=bottom-left corner
        for direction in range(4):
            pulse = {
                "direction": direction,
                "progress": 0.0,  # 0 to 1
                "speed": 1.0 / min(0.5, self.measured_beat_interval)  # Minimum speed at 120 BPM
            }
            self.pulses.append(pulse)

    def update(self, dt_ms, energies, sensitivity, flash_thresh):
        # Track mid energy
        self.mid_energy = energies.get('mid', 0.0) * sensitivity

        dt_sec = dt_ms / 1000.0

        # Update hue shift based on mid energy
        self.hue_shift += self.mid_energy * dt_sec * 360.0
        self.hue_shift %= 360.0

        # Update all pulses
        for pulse in self.pulses[:]:
            pulse["progress"] += pulse["speed"] * dt_sec

            # Remove pulses that have completed
            if pulse["progress"] >= 1.0:
                self.pulses.remove(pulse)

    def paint(self, p: QPainter, brightness: float):
        p.save()
        p.setRenderHint(QPainter.Antialiasing, True)

        w, h = self.size.width(), self.size.height()
        cx, cy = w / 2.0, h / 2.0

        # Color - apply hue shift based on mids
        base_hsv = self.base_color.toHsv()
        hue, sat, val, alpha = base_hsv.getHsv()

        # Shift hue
        new_hue = (hue + self.hue_shift) % 360
        color = QColor.fromHsv(int(new_hue), sat, val, alpha)
        color.setAlphaF(max(0.0, min(1.0, brightness)))

        # Draw the main X lines (2px wide)
        pen = QPen(color, 2)
        p.setPen(pen)

        # Diagonal line from top-left to bottom-right
        p.drawLine(QPointF(0, 0), QPointF(w, h))

        # Diagonal line from top-right to bottom-left
        p.drawLine(QPointF(w, 0), QPointF(0, h))

        # Draw white pulses (bright and highly visible on colored lines)
        white_pen = QPen(QColor(255, 255, 255), 8)
        p.setPen(white_pen)

        pulse_length = 80.0  # Increased from 50 to be more visible

        for pulse in self.pulses:
            direction = pulse["direction"]
            progress = pulse["progress"]

            # Define the corner endpoints for each direction
            # Line 1: (0,0) to (w,h) - directions 0 and 1
            # Line 2: (w,0) to (0,h) - directions 2 and 3
            if direction == 0:  # Toward top-left corner (0,0)
                corner_x, corner_y = 0, 0
            elif direction == 1:  # Toward bottom-right corner (w,h)
                corner_x, corner_y = w, h
            elif direction == 2:  # Toward top-right corner (w,0)
                corner_x, corner_y = w, 0
            else:  # direction == 3: Toward bottom-left corner (0,h)
                corner_x, corner_y = 0, h

            # Calculate the direction vector from center to corner
            dx = corner_x - cx
            dy = corner_y - cy
            line_length = math.sqrt(dx * dx + dy * dy)

            # Current position along the line (0 = center, 1 = corner)
            current_x = cx + dx * progress
            current_y = cy + dy * progress

            # Calculate pulse start and end positions along the line
            # Pulse is centered at current position, extends pulse_length/2 in each direction
            pulse_half = pulse_length / 2.0

            # Start of pulse (closer to center)
            progress_start = max(0.0, progress - pulse_half / line_length)
            start_x = cx + dx * progress_start
            start_y = cy + dy * progress_start

            # End of pulse (closer to corner)
            progress_end = min(1.0, progress + pulse_half / line_length)
            end_x = cx + dx * progress_end
            end_y = cy + dy * progress_end

            # Draw the pulse
            p.drawLine(QPointF(start_x, start_y), QPointF(end_x, end_y))

        p.restore()
