import time
import random
import math
from PySide6.QtCore import QSize, QPointF, Qt
from PySide6.QtGui import QPainter, QColor, QPen
from ..effect_base import Effect


class CornerBurst(Effect):
    """
    Corner Burst Effect:
    - Lines shoot from screen corners toward center, then retract
    - Bass controls line length/speed
    - Mids control number of lines per corner (1-5)
    - Highs control line thickness
    - Beat rotates which corners are active (all → diagonals → sides → cycle)
    - 200ms beat debounce
    """

    name = "Corner Burst"
    effect_class = "cornereffect_class01"

    def __init__(self, size: QSize):
        super().__init__(size)

        # Beat debounce
        self.last_beat_time = 0.0
        self.beat_debounce_ms = 200

        # Animation state
        self.phase = 0.0  # 0 to 1 (shoot out), 1 to 0 (retract)
        self.extending = True

        # Corner activation mode
        # 0 = all corners, 1 = diagonals only (TL, BR), 2 = sides only (TR, BL)
        self.corner_mode = 0

        # Energy tracking
        self.bass_energy = 0.0
        self.mid_energy = 0.0
        self.high_energy = 0.0

        # Corner positions (will be set in paint based on size)
        self.corners = {
            "TL": {"active": True, "angle_range": (0, 90)},      # Top-left
            "TR": {"active": True, "angle_range": (90, 180)},    # Top-right
            "BR": {"active": True, "angle_range": (180, 270)},   # Bottom-right
            "BL": {"active": True, "angle_range": (270, 360)},   # Bottom-left
        }

    def on_beat(self):
        # Debounce
        now = time.time()
        if (now - self.last_beat_time) * 1000.0 < self.beat_debounce_ms:
            return

        self.last_beat_time = now

        super().on_beat()

        # Cycle corner mode
        self.corner_mode = (self.corner_mode + 1) % 3

        # Update active corners based on mode
        if self.corner_mode == 0:
            # All corners
            for corner in self.corners.values():
                corner["active"] = True
        elif self.corner_mode == 1:
            # Diagonals only (TL, BR)
            self.corners["TL"]["active"] = True
            self.corners["TR"]["active"] = False
            self.corners["BR"]["active"] = True
            self.corners["BL"]["active"] = False
        else:  # mode == 2
            # Sides only (TR, BL)
            self.corners["TL"]["active"] = False
            self.corners["TR"]["active"] = True
            self.corners["BR"]["active"] = False
            self.corners["BL"]["active"] = True

    def update(self, dt_ms, energies, sensitivity, flash_thresh):
        # Track energies
        self.bass_energy = energies.get('low', 0.0) * sensitivity
        self.mid_energy = energies.get('mid', 0.0) * sensitivity
        self.high_energy = energies.get('high', 0.0) * sensitivity

        dt_sec = dt_ms / 1000.0

        # Speed based on bass
        speed = 0.8 + self.bass_energy * 1.5

        # Update phase
        if self.extending:
            self.phase += speed * dt_sec
            if self.phase >= 1.0:
                self.phase = 1.0
                self.extending = False
        else:
            self.phase -= speed * dt_sec * 0.8  # Retract slightly slower
            if self.phase <= 0.0:
                self.phase = 0.0
                self.extending = True

    def paint(self, p: QPainter, brightness: float):
        p.save()
        p.setRenderHint(QPainter.Antialiasing, True)

        w, h = self.size.width(), self.size.height()
        cx, cy = w / 2.0, h / 2.0

        # Maximum line length (from corner to center)
        max_length = math.sqrt(cx * cx + cy * cy)

        # Current line length based on phase and bass
        current_length = max_length * self.phase * (0.5 + self.bass_energy * 0.5)

        # Number of lines per corner based on mids
        num_lines = int(1 + self.mid_energy * 4)
        num_lines = max(1, min(num_lines, 5))

        # Line thickness from highs
        line_width = 1.5 + self.high_energy * 4.0

        # Corner positions
        corner_positions = {
            "TL": (0, 0),
            "TR": (w, 0),
            "BR": (w, h),
            "BL": (0, h)
        }

        for corner_name, (corner_x, corner_y) in corner_positions.items():
            corner_data = self.corners[corner_name]

            if not corner_data["active"]:
                continue

            # Direction from corner to center
            dx = cx - corner_x
            dy = cy - corner_y
            base_angle = math.atan2(dy, dx)

            # Spread lines in a fan pattern
            angle_spread = math.pi / 6  # 30 degrees total spread

            for i in range(num_lines):
                # Calculate angle for this line
                if num_lines == 1:
                    angle = base_angle
                else:
                    offset = (i / (num_lines - 1) - 0.5) * angle_spread
                    angle = base_angle + offset

                # End point of line
                end_x = corner_x + current_length * math.cos(angle)
                end_y = corner_y + current_length * math.sin(angle)

                # Color - different for each corner
                if corner_name == "TL":
                    color = QColor(255, 100, 100)  # Red
                elif corner_name == "TR":
                    color = QColor(100, 255, 100)  # Green
                elif corner_name == "BR":
                    color = QColor(100, 100, 255)  # Blue
                else:  # BL
                    color = QColor(255, 255, 100)  # Yellow

                # Apply brightness and phase fade
                alpha = brightness * (0.5 + self.phase * 0.5)
                color.setAlphaF(max(0.0, min(1.0, alpha)))

                pen = QPen(color, line_width)
                pen.setCapStyle(Qt.RoundCap)
                p.setPen(pen)

                p.drawLine(
                    QPointF(corner_x, corner_y),
                    QPointF(end_x, end_y)
                )

        p.restore()
