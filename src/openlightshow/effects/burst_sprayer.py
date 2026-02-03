from PySide6.QtCore import QSize, QPointF
from PySide6.QtGui import QPainter, QColor, QPen
from ..effect_base import Effect
import math
import time
import random


class BurstSprayer(Effect):
    """
    BurstSprayer effect:
    - Machine gun-like particle spray effect
    - Fires from center top or bottom (alternates every 8 beats)
    - Each beat fires many colorful particles
    - Particles spray in a sweeping arc pattern (like waving a machine gun)
    - Flying particles similar to Wild Shot
    - Painter state is isolated with save/restore
    """
    name = "BurstSprayer"
    effect_class = "particle_class01"

    def __init__(self, size: QSize):
        super().__init__(size)
        self.size = size

        # Firing position
        self.fire_from_top = True  # True = top, False = bottom
        self.fire_x = size.width() / 2
        self.fire_y = 0

        # Particle properties
        self.particles = []  # List of active particles
        self.particle_length = 30.0  # Length of particle trail
        self.particle_width = 4.0

        # Machine gun spray pattern
        self.particles_per_beat = 25  # Particles for spray effect (reduced by half)
        self.spray_arc = math.pi * 0.8  # 144 degrees arc (0.8 * 180°)

        # Sweep animation
        self.sweep_offset = 0.0  # Current sweep angle offset
        self.sweep_speed = 3.0  # Radians per second
        self.sweep_direction = 1  # 1 or -1

        # Beat tracking
        self.beat_counter = 0
        self.last_beat_time = -1000
        self.beat_cooldown_ms = 300  # 300ms debounce to prevent double beats

        # Neon colors (from Wild Shot)
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

    def resize(self, size: QSize):
        super().resize(size)
        self.size = size
        self._update_fire_position()

    def _update_fire_position(self):
        """Update firing position based on current orientation."""
        self.fire_x = self.size.width() / 2
        if self.fire_from_top:
            self.fire_y = 0
        else:
            self.fire_y = self.size.height()

    def on_beat(self):
        """Trigger particle spray on beat."""
        super().on_beat()
        now = time.time() * 1000
        if now - self.last_beat_time >= self.beat_cooldown_ms:
            self.last_beat_time = now

            # Increment beat counter
            self.beat_counter += 1

            # Switch firing position every 8 beats
            if self.beat_counter % 8 == 0:
                self.fire_from_top = not self.fire_from_top
                self._update_fire_position()
                # Reverse sweep direction on position change
                self.sweep_direction *= -1

            # Fire particle spray
            self._fire_spray()

    def _fire_spray(self):
        """Fire a spray of particles in an arc pattern."""
        # Base angle depends on firing position
        if self.fire_from_top:
            base_angle = math.pi / 2  # Downward (90°)
        else:
            base_angle = -math.pi / 2  # Upward (-90°)

        # Add sweep offset
        center_angle = base_angle + self.sweep_offset

        # Fire particles spread across the arc
        for i in range(self.particles_per_beat):
            # Calculate angle within the spray arc
            # Spread particles across the arc with some randomness
            spread = (i / self.particles_per_beat - 0.5) * self.spray_arc
            angle = center_angle + spread + random.uniform(-0.1, 0.1)

            # Random speed variation
            speed = random.uniform(0.8, 1.2)

            # Random neon color
            color = random.choice(self.neon_colors)

            particle = {
                'x': self.fire_x,
                'y': self.fire_y,
                'angle': angle,
                'speed': speed * 1600.0,  # pixels per second (4x faster: 400 * 4 = 1600)
                'progress': 0.0,
                'color': color,
                'max_distance': math.sqrt(self.size.width()**2 + self.size.height()**2)
            }

            self.particles.append(particle)

    def update(self, dt_ms: int, energies: dict, sensitivity: float, flash_thresh: float):
        """Update sweep angle and particle positions."""
        dt_sec = dt_ms / 1000.0

        # Update sweep offset (machine gun waving motion)
        self.sweep_offset += self.sweep_speed * self.sweep_direction * dt_sec
        # Keep sweep within bounds
        max_sweep = self.spray_arc / 2
        if abs(self.sweep_offset) > max_sweep:
            self.sweep_direction *= -1
            self.sweep_offset = max_sweep * self.sweep_direction

        # Update particles
        particles_to_remove = []
        for i, particle in enumerate(self.particles):
            # Update position
            particle['x'] += math.cos(particle['angle']) * particle['speed'] * dt_sec
            particle['y'] += math.sin(particle['angle']) * particle['speed'] * dt_sec

            # Update progress based on distance traveled
            dx = particle['x'] - self.fire_x
            dy = particle['y'] - self.fire_y
            distance = math.sqrt(dx * dx + dy * dy)
            particle['progress'] = min(1.0, distance / particle['max_distance'])

            # Remove if off screen or fully faded
            if particle['progress'] >= 1.0:
                particles_to_remove.append(i)
            elif (particle['x'] < -100 or particle['x'] > self.size.width() + 100 or
                  particle['y'] < -100 or particle['y'] > self.size.height() + 100):
                particles_to_remove.append(i)

        # Remove expired particles
        for i in reversed(particles_to_remove):
            self.particles.pop(i)

    def paint(self, painter: QPainter, brightness: float):
        """Draw the BurstSprayer particles."""
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)

        for particle in self.particles:
            # Calculate particle trail endpoints
            angle = particle['angle']
            dx = math.cos(angle)
            dy = math.sin(angle)

            particle_half = self.particle_length / 2.0

            # Particle center
            cx = particle['x']
            cy = particle['y']

            # Start and end of particle trail
            start_x = cx - dx * particle_half
            start_y = cy - dy * particle_half
            end_x = cx + dx * particle_half
            end_y = cy + dy * particle_half

            # Color with fade based on progress
            color = QColor(particle['color'])
            # Fade out as particle travels
            alpha = brightness * (1.0 - particle['progress'] * 0.6)
            color.setAlphaF(max(0.0, min(1.0, alpha)))

            pen = QPen(color, self.particle_width)
            painter.setPen(pen)

            # Draw the particle
            painter.drawLine(
                QPointF(start_x, start_y),
                QPointF(end_x, end_y)
            )

        painter.restore()
