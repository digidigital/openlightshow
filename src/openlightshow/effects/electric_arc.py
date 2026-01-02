import time
import random
import math
from PySide6.QtCore import QSize, QPointF, Qt
from PySide6.QtGui import QPainter, QColor, QPen
from ..effect_base import Effect


class ElectricArc(Effect):
    """
    Electric Arc Effect:
    - Lightning bolts that arc across the screen
    - Bass triggers new lightning bolts
    - Mids control branching frequency
    - Highs control bolt jaggedness
    - Beat creates multi-point lightning
    - 200ms beat debounce
    """

    name = "Electric Arc"
    effect_class = "lightningeffect_class01"

    def __init__(self, size: QSize):
        super().__init__(size)

        # Beat debounce
        self.last_beat_time = 0.0
        self.beat_debounce_ms = 200

        # Lightning bolts: list of dicts
        self.bolts = []

        # Energy tracking
        self.bass_energy = 0.0
        self.mid_energy = 0.0
        self.high_energy = 0.0

        # Beat interval tracking for bolt lifetime
        self.beat_times = []
        self.max_beat_history = 4
        self.measured_beat_interval = 0.5  # Initial guess

        # Arc colors (electric blue/cyan/white)
        self.arc_colors = [
            QColor(100, 150, 255),  # electric blue
            QColor(150, 200, 255),  # light blue
            QColor(200, 230, 255),  # very light blue
            QColor(255, 255, 255),  # white
        ]

    def on_beat(self):
        # Debounce
        now = time.time()
        if (now - self.last_beat_time) * 1000.0 < self.beat_debounce_ms:
            return

        # Track beat timing
        self.beat_times.append(now)
        if len(self.beat_times) > self.max_beat_history:
            self.beat_times.pop(0)

        # Calculate average beat interval
        if len(self.beat_times) >= 2:
            intervals = [self.beat_times[i] - self.beat_times[i-1]
                        for i in range(1, len(self.beat_times))]
            self.measured_beat_interval = sum(intervals) / len(intervals)

        self.last_beat_time = now

        super().on_beat()

        # Create multi-point lightning on beat (3-5 simultaneous bolts)
        num_bolts = random.randint(3, 5)
        for _ in range(num_bolts):
            self._create_bolt()

    def _create_bolt(self):
        """Create a single lightning bolt"""
        w, h = self.size.width(), self.size.height()

        # Random start and end points
        start = QPointF(random.uniform(0, w), random.uniform(0, h))
        end = QPointF(random.uniform(0, w), random.uniform(0, h))

        bolt = {
            "start": start,
            "end": end,
            "progress": 0.0,
            "lifetime": min(0.3, self.measured_beat_interval * 0.6),  # 60% of beat interval, max 0.3s
            "color": random.choice(self.arc_colors),
            "segments": self._generate_segments(start, end)
        }
        self.bolts.append(bolt)

    def _generate_segments(self, start, end):
        """Generate jagged lightning segments"""
        # Jaggedness based on high energy (more jagged = more segments)
        num_segments = int(5 + self.high_energy * 15)
        num_segments = max(5, min(num_segments, 20))

        # Branching probability based on mid energy
        branch_prob = self.mid_energy * 0.3  # 0-30% chance

        segments = []
        dx = (end.x() - start.x()) / num_segments
        dy = (end.y() - start.y()) / num_segments

        current = QPointF(start)

        for i in range(num_segments):
            # Calculate next point with jaggedness
            next_x = start.x() + (i + 1) * dx
            next_y = start.y() + (i + 1) * dy

            # Add random offset perpendicular to the line
            offset_amount = self.high_energy * 20.0
            angle = math.atan2(dy, dx) + math.pi / 2
            offset_x = random.uniform(-offset_amount, offset_amount) * math.cos(angle)
            offset_y = random.uniform(-offset_amount, offset_amount) * math.sin(angle)

            next_point = QPointF(next_x + offset_x, next_y + offset_y)
            segments.append((QPointF(current), next_point))

            # Maybe create a branch
            if random.random() < branch_prob and i > 2 and i < num_segments - 2:
                # Create a short branch
                branch_end = QPointF(
                    current.x() + random.uniform(-50, 50),
                    current.y() + random.uniform(-50, 50)
                )
                segments.append((QPointF(current), branch_end))

            current = next_point

        return segments

    def update(self, dt_ms, energies, sensitivity, flash_thresh):
        # Track energies
        self.bass_energy = energies.get('low', 0.0) * sensitivity
        self.mid_energy = energies.get('mid', 0.0) * sensitivity
        self.high_energy = energies.get('high', 0.0) * sensitivity

        dt_sec = dt_ms / 1000.0

        # Trigger new bolt on strong bass
        if self.bass_energy > 0.7:
            if random.random() < 0.1:  # 10% chance per frame when bass is strong
                self._create_bolt()

        # Update all bolts
        for bolt in self.bolts[:]:
            bolt["progress"] += dt_sec

            # Remove bolts that have expired
            if bolt["progress"] >= bolt["lifetime"]:
                self.bolts.remove(bolt)

    def paint(self, p: QPainter, brightness: float):
        p.save()
        p.setRenderHint(QPainter.Antialiasing, True)

        for bolt in self.bolts:
            # Fade out as bolt ages
            age_factor = 1.0 - (bolt["progress"] / bolt["lifetime"])

            color = QColor(bolt["color"])
            alpha = brightness * age_factor
            color.setAlphaF(max(0.0, min(1.0, alpha)))

            # Thicker lines when bass is strong
            line_width = 2.0 + self.bass_energy * 2.0
            pen = QPen(color, line_width)
            p.setPen(pen)

            # Draw all segments
            for start, end in bolt["segments"]:
                p.drawLine(start, end)

        p.restore()
