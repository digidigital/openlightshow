import time
import random
import math
from PySide6.QtCore import QSize, QPointF, Qt
from PySide6.QtGui import QPainter, QColor, QPen
from ..effect_base import Effect


class WildShot(Effect):
    """
    WildShot Effect:
    - Each beat fires particles from the center in random directions
    - Each particle has a unique neon color
    - Particle directions change randomly with each beat
    - Particles travel outward and fade as they reach the edges
    - 200ms beat debounce
    """

    name = "Wild Shot"
    effect_class = "particle_class01"

    def __init__(self, size: QSize):
        super().__init__(size)

        # Beat debounce
        self.last_beat_time = 0.0
        self.beat_debounce_ms = 200

        # Beat interval tracking for particle speed
        self.beat_times = []
        self.max_beat_history = 4
        self.measured_beat_interval = 0.5  # Initial guess (120 BPM)

        # Particles: list of dicts with angle, progress, color
        self.particles = []

        # Number of particles to shoot per beat
        self.particles_per_beat = 12

        # Particle size
        self.particle_length = 25.0
        self.particle_width = 5.0

        # Neon colors
        self.neon_colors = [
            QColor(57, 255, 20),    # neon green
            QColor(255, 20, 147),   # neon pink
            QColor(0, 255, 255),    # neon cyan
            QColor(255, 255, 0),    # neon yellow
            QColor(255, 0, 255),    # neon magenta
            QColor(255, 165, 0),    # neon orange
            QColor(0, 255, 128),    # neon lime
            QColor(255, 50, 255),   # bright purple
            QColor(255, 100, 100),  # bright red
            QColor(100, 255, 255),  # bright cyan
            QColor(255, 255, 100),  # bright yellow
            QColor(100, 255, 100),  # bright green
        ]

        # Energy tracking
        self.bass_energy = 0.0

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

        # Create particles in random directions
        for _ in range(self.particles_per_beat):
            # Random angle (0 to 2π)
            angle = random.uniform(0, 2 * math.pi)

            # Random neon color
            color = random.choice(self.neon_colors)

            particle = {
                "angle": angle,
                "progress": 0.0,  # 0 to 1
                "speed": 1.0 / min(0.5, self.measured_beat_interval),  # Minimum speed at 120 BPM
                "color": color
            }
            self.particles.append(particle)

    def update(self, dt_ms, energies, sensitivity, flash_thresh):
        # Track bass energy
        self.bass_energy = energies.get('low', 0.0) * sensitivity

        dt_sec = dt_ms / 1000.0

        # Update all particles
        for particle in self.particles[:]:
            particle["progress"] += particle["speed"] * dt_sec

            # Remove particles that have completed
            if particle["progress"] >= 1.0:
                self.particles.remove(particle)

    def paint(self, p: QPainter, brightness: float):
        p.save()
        p.setRenderHint(QPainter.Antialiasing, True)

        w, h = self.size.width(), self.size.height()
        cx, cy = w / 2.0, h / 2.0

        # Calculate maximum distance from center to edge (to any corner)
        max_dist = math.sqrt(cx * cx + cy * cy)

        # Particle width based on bass energy
        current_width = self.particle_width + self.bass_energy * 3.0

        for particle in self.particles:
            angle = particle["angle"]
            progress = particle["progress"]

            # Calculate direction vector
            dx = math.cos(angle)
            dy = math.sin(angle)

            # Current position along the direction (0 = center, max_dist = edge)
            current_dist = progress * max_dist

            # Calculate particle start and end positions
            # Particle is centered at current position, extends particle_length/2 in each direction
            particle_half = self.particle_length / 2.0

            # Start of particle (closer to center)
            start_dist = max(0.0, current_dist - particle_half)
            start_x = cx + dx * start_dist
            start_y = cy + dy * start_dist

            # End of particle (closer to edge)
            end_dist = current_dist + particle_half
            end_x = cx + dx * end_dist
            end_y = cy + dy * end_dist

            # Color with brightness and fade based on progress
            color = QColor(particle["color"])
            # Fade out as particle approaches edge
            alpha = brightness * (1.0 - progress * 0.5)  # Keep some visibility even at edge
            color.setAlphaF(max(0.0, min(1.0, alpha)))

            pen = QPen(color, current_width)
            p.setPen(pen)

            # Draw the particle
            p.drawLine(QPointF(start_x, start_y), QPointF(end_x, end_y))

        p.restore()
