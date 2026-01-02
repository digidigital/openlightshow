import time
import random
import math
from PySide6.QtCore import QSize, QPointF, Qt
from PySide6.QtGui import QPainter, QColor, QPen, QBrush
from ..effect_base import Effect


class CircleConstellations(Effect):
    """
    CircleConstellations Effect:
    - Small circles connected by lines like star constellations
    - Circles slowly drift and reconnect to nearest neighbors
    - Beat triggers constellation reconfiguration
    - Line brightness based on distance between circles
    - 4-way mirror creates symmetrical patterns
    - 200ms beat debounce
    """

    name = "Circle Constellations"
    effect_class = "particle_class01"

    def __init__(self, size: QSize):
        super().__init__(size)

        # Beat debounce
        self.last_beat_time = 0.0
        self.beat_debounce_ms = 200

        # Circles (nodes in constellation) - work in top-left quadrant
        self.circles = []

        # Energy tracking
        self.mid_energy = 0.0

        # Drift speed
        self.drift_speed = 50.0  # pixels per second

        # Connection distance threshold
        self.connection_distance = 200.0

        # Neon colors
        self.neon_colors = [
            QColor(57, 255, 20),    # neon green
            QColor(255, 20, 147),   # neon pink
            QColor(0, 255, 255),    # neon cyan
            QColor(255, 255, 0),    # neon yellow
            QColor(255, 0, 255),    # neon magenta
            QColor(255, 165, 0),    # neon orange
        ]

        self.current_color = random.choice(self.neon_colors)

        # Spawn initial constellation
        self.spawn_constellation()

    def spawn_constellation(self):
        """Spawn circles in random positions (top-left quadrant)."""
        self.circles = []
        w, h = self.size.width(), self.size.height()
        quad_w, quad_h = w / 2, h / 2

        # Number of circles
        num_circles = random.randint(6, 10)

        margin = 50

        for _ in range(num_circles):
            # Random position in top-left quadrant
            x = random.uniform(margin, quad_w - margin)
            y = random.uniform(margin, quad_h - margin)

            # Random drift velocity
            angle = random.uniform(0, 2 * math.pi)
            vx = math.cos(angle) * self.drift_speed
            vy = math.sin(angle) * self.drift_speed

            circle = {
                "x": x,
                "y": y,
                "vx": vx,
                "vy": vy,
                "radius": random.uniform(3, 6)
            }
            self.circles.append(circle)

    def on_beat(self):
        # Debounce: ignore beats too close together
        now = time.time() * 200.0
        if now - self.last_beat_time < self.beat_debounce_ms:
            return
        self.last_beat_time = now

        super().on_beat()

        # Reconfigure constellation on beat
        self.spawn_constellation()

        # Change color on beat
        self.current_color = random.choice(self.neon_colors)

    def update(self, dt_ms, energies, sensitivity, flash_thresh):
        # Track mid energy
        self.mid_energy = energies.get('mid', 0.0) * sensitivity

        dt_sec = dt_ms / 1000.0
        w, h = self.size.width(), self.size.height()
        quad_w, quad_h = w / 2, h / 2

        margin = 50

        # Update all circles
        for circle in self.circles:
            # Drift
            circle["x"] += circle["vx"] * dt_sec
            circle["y"] += circle["vy"] * dt_sec

            # Bounce off quadrant boundaries
            if circle["x"] < margin or circle["x"] > quad_w - margin:
                circle["vx"] *= -1
                circle["x"] = max(margin, min(quad_w - margin, circle["x"]))

            if circle["y"] < margin or circle["y"] > quad_h - margin:
                circle["vy"] *= -1
                circle["y"] = max(margin, min(quad_h - margin, circle["y"]))

    def paint(self, p: QPainter, brightness: float):
        if not self.circles:
            return

        p.save()
        p.setRenderHint(QPainter.Antialiasing, True)

        w, h = self.size.width(), self.size.height()
        cx, cy = w / 2, h / 2

        # Color with brightness
        color = QColor(self.current_color)
        color.setAlphaF(max(0.0, min(1.0, brightness)))

        # Draw in all 4 quadrants (mirror effect)
        for quad_dx, quad_dy in [(1, 1), (-1, 1), (1, -1), (-1, -1)]:
            # Draw connection lines first (so circles are on top)
            for i, circle1 in enumerate(self.circles):
                for circle2 in self.circles[i+1:]:
                    # Calculate distance
                    dx = circle2["x"] - circle1["x"]
                    dy = circle2["y"] - circle1["y"]
                    distance = math.sqrt(dx * dx + dy * dy)

                    # Only connect if within threshold
                    if distance < self.connection_distance:
                        # Line brightness based on distance (closer = brighter)
                        line_alpha = brightness * (1.0 - distance / self.connection_distance)

                        line_color = QColor(color)
                        line_color.setAlphaF(max(0.0, min(1.0, line_alpha)))

                        # Line width based on mid energy
                        line_width = 1.0 + self.mid_energy * 2.0

                        p.setPen(QPen(line_color, line_width))

                        # Mirror positions
                        x1 = cx + quad_dx * circle1["x"]
                        y1 = cy + quad_dy * circle1["y"]
                        x2 = cx + quad_dx * circle2["x"]
                        y2 = cy + quad_dy * circle2["y"]

                        p.drawLine(QPointF(x1, y1), QPointF(x2, y2))

            # Draw circles
            p.setPen(QPen(color, 2))
            p.setBrush(QBrush(color))

            for circle in self.circles:
                # Mirror position
                x = cx + quad_dx * circle["x"]
                y = cy + quad_dy * circle["y"]

                p.drawEllipse(QPointF(x, y), circle["radius"], circle["radius"])

        p.restore()
