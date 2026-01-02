"""
DiscoBall effect - Disco ball square light reflections (projection only).

Behavior:
- Small square reflections move quickly from left to right (and reverse)
- Reflections fade over time and have physics (gravity, bouncing)
- Simulates square mirror reflections from a rotating disco ball
- Bass: Spawns new reflections
- Mids: Reflection movement speed
- Highs: Reflection brightness and spawn rate
- Beat: Creates burst of reflections and changes colors
"""

import math
import time
import random
from PySide6.QtCore import QPointF, QSize, QRectF
from PySide6.QtGui import QPainter, QColor, QPen, QRadialGradient
from ..effect_base import Effect


class ReflectionSpot:
    """A single light reflection from the disco ball."""
    def __init__(self, x, y, vx, vy, hue, size):
        self.x = x
        self.y = y
        self.vx = vx  # Velocity x
        self.vy = vy  # Velocity y
        self.hue = hue
        self.size = size
        self.life = 1.0  # 1.0 = just spawned, 0.0 = dead
        self.max_life = random.uniform(0.8, 2.0)  # Seconds to live


class DiscoBallEffect(Effect):
    name = "DiscoBall"
    effect_class = "particle_class01"

    def __init__(self, size: QSize):
        super().__init__(size)
        self.reflections = []
        self.hue_base = 0.0

        # Music reactive values
        self.bass_energy = 0.0
        self.mid_energy = 0.0
        self.high_energy = 0.0

        # Beat detection
        self.last_beat_time = 0.0
        self.beat_pulse = 0.0

        # Spawn timing
        self.spawn_accumulator = 0.0

    def on_beat(self):
        """Triggered on beat detection."""
        current_time = time.time() * 1000.0

        # Debounce beats (200ms)
        if current_time - self.last_beat_time < 200:
            return

        self.last_beat_time = current_time
        self.beat_pulse = 1.0

        # Create burst of reflections on beat
        self._spawn_reflection_burst(10, 15)

        # Change base hue
        self.hue_base = (self.hue_base + random.uniform(0.1, 0.3)) % 1.0

    def _spawn_reflection_burst(self, min_count, max_count):
        """Spawn multiple reflections at once."""
        count = random.randint(min_count, max_count)
        w, h = self.size.width(), self.size.height()

        for _ in range(count):
            # Spawn from random position
            origin_x = random.uniform(0, w)
            origin_y = random.uniform(0, h)
            self._spawn_reflection(origin_x, origin_y)

    def _spawn_reflection(self, origin_x, origin_y):
        """Spawn a single reflection."""
        w, h = self.size.width(), self.size.height()

        # All movement is left to right only
        speed = random.uniform(400, 1000)  # Fast horizontal movement (2x speed)
        vx = speed  # Always positive (left to right)
        vy = 0  # No vertical movement

        # Random hue near the base hue
        hue = (self.hue_base + random.uniform(-0.1, 0.1)) % 1.0

        # Larger square size (2x original)
        size = random.uniform(20, 50)

        reflection = ReflectionSpot(origin_x, origin_y, vx, vy, hue, size)
        self.reflections.append(reflection)

    def update(self, dt_ms, energies, sensitivity, flash_thresh):
        """Update effect state."""
        dt_sec = dt_ms / 1000.0

        # Extract energy values
        self.bass_energy = energies.get('low', 0.0) * sensitivity
        self.mid_energy = energies.get('mid', 0.0) * sensitivity
        self.high_energy = energies.get('high', 0.0) * sensitivity

        # Spawn reflections based on high energy and bass
        spawn_rate = 3.0 + self.high_energy * 10.0 + self.bass_energy * 6.0  # Per second
        self.spawn_accumulator += spawn_rate * dt_sec

        w, h = self.size.width(), self.size.height()

        while self.spawn_accumulator >= 1.0:
            # Spawn from random position
            origin_x = random.uniform(0, w)
            origin_y = random.uniform(0, h)
            self._spawn_reflection(origin_x, origin_y)
            self.spawn_accumulator -= 1.0

        # Speed multiplier from mids
        speed_mult = 1.0 + self.mid_energy * 1.5

        # Update reflections
        for reflection in self.reflections[:]:
            # Move with speed multiplier
            reflection.x += reflection.vx * dt_sec * speed_mult
            reflection.y += reflection.vy * dt_sec * speed_mult

            # Remove reflections that go off the right edge
            if reflection.x > w:
                self.reflections.remove(reflection)
                continue

            # Decay life
            reflection.life -= dt_sec / reflection.max_life

            # Remove dead reflections
            if reflection.life <= 0:
                self.reflections.remove(reflection)

        # Limit number of reflections for performance
        max_reflections = 120
        if len(self.reflections) > max_reflections:
            # Remove oldest (first in list)
            self.reflections = self.reflections[-max_reflections:]

        # Decay beat pulse
        if self.beat_pulse > 0:
            self.beat_pulse -= dt_sec * 3.0
            self.beat_pulse = max(0.0, self.beat_pulse)

        # Slow hue drift
        self.hue_base += dt_sec * 0.02
        self.hue_base = self.hue_base % 1.0

    def paint(self, p: QPainter, brightness: float):
        """Render the disco ball reflections."""
        p.save()

        # Draw all reflections
        for reflection in self.reflections:
            self._draw_reflection(p, reflection, brightness)

        p.restore()

    def _draw_reflection(self, p: QPainter, reflection, brightness_val):
        """Draw a single square light reflection."""
        # Fade based on life
        alpha = reflection.life * brightness_val
        intensity = min(1.0, 0.8 + self.high_energy * 0.2 + self.beat_pulse * 0.3)

        # Square color with gradient effect
        square_color = QColor.fromHsvF(reflection.hue, 0.6, intensity)
        square_alpha = max(0.0, min(1.0, alpha * 0.9))
        square_color.setAlphaF(square_alpha)

        # Draw square (no rotation)
        p.save()

        # Draw outer glow (larger semi-transparent square)
        glow_size = reflection.size * 1.3
        glow_color = QColor.fromHsvF(reflection.hue, 0.7, 0.6)
        glow_alpha = max(0.0, min(1.0, alpha * 0.3))
        glow_color.setAlphaF(glow_alpha)

        p.setPen(QPen(QColor(0, 0, 0, 0)))
        p.setBrush(glow_color)
        glow_rect = QRectF(reflection.x - glow_size / 2, reflection.y - glow_size / 2, glow_size, glow_size)
        p.drawRect(glow_rect)

        # Draw main square
        p.setBrush(square_color)
        square_rect = QRectF(reflection.x - reflection.size / 2, reflection.y - reflection.size / 2, reflection.size, reflection.size)
        p.drawRect(square_rect)

        # Draw brighter core (small inner square)
        core_size = reflection.size * 0.5
        core_color = QColor.fromHsvF(reflection.hue, 0.3, 1.0)
        core_alpha = max(0.0, min(1.0, alpha * 0.95))
        core_color.setAlphaF(core_alpha)
        p.setBrush(core_color)
        core_rect = QRectF(reflection.x - core_size / 2, reflection.y - core_size / 2, core_size, core_size)
        p.drawRect(core_rect)

        p.restore()
