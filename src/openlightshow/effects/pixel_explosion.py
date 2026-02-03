import time
import random
import math
from PySide6.QtCore import QSize, QPointF, Qt
from PySide6.QtGui import QPainter, QColor, QPen, QBrush
from ..effect_base import Effect


class PixelExplosion(Effect):
    """
    PixelExplosion Effect:
    - On each beat, spawn a burst of 4x4 bright pixels from a random location
    - Pixels expand outward in all directions at high speed
    - Pixels slow down and fade over time (momentum-based)
    - Color varies by frequency energy
    - Multiple explosions can overlap
    - 200ms beat debounce for safety
    """

    name = "Pixel Explosion"
    effect_class = "particle_class01"

    def __init__(self, size: QSize):
        super().__init__(size)
        self.explosions = []  # list of explosion dicts

        # Beat debounce (safe 200ms)
        self.last_beat_time = 0.0
        self.beat_debounce_ms = 200

        # Energy tracking for colors
        self.low_energy = 0.0
        self.mid_energy = 0.0
        self.high_energy = 0.0

        # Bright neon colors
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
        ]

    def on_beat(self):
        # Debounce: ignore beats too close together
        now = time.time() * 1000.0
        if now - self.last_beat_time < self.beat_debounce_ms:
            return
        self.last_beat_time = now

        super().on_beat()

        # Random explosion location
        w, h = self.size.width(), self.size.height()
        margin = 100  # Keep away from edges
        ex = random.uniform(margin, w - margin)
        ey = random.uniform(margin, h - margin)

        # Choose color based on current frequency energy
        # High energy = brighter/warmer colors
        if self.high_energy > 0.6:
            base_color = random.choice([QColor(255, 255, 0), QColor(255, 0, 255), QColor(0, 255, 255)])
        elif self.mid_energy > 0.5:
            base_color = random.choice([QColor(57, 255, 20), QColor(255, 165, 0)])
        else:
            base_color = random.choice(self.neon_colors)

        # Create 4x4 grid of pixels (16 pixels total)
        pixels = []
        pixel_size = 8  # 8x8 pixels

        # High explosion speed
        base_speed = 300  # pixels per second
        speed_variance = 100

        # Create pixels in a 4x4 grid pattern
        for row in range(4):
            for col in range(4):
                # Calculate angle from explosion center to this pixel position
                # This creates a radial burst pattern
                offset_x = (col - 1.5) * 3  # Center the grid
                offset_y = (row - 1.5) * 3

                # Calculate velocity direction
                angle = math.atan2(offset_y, offset_x)
                speed = base_speed + random.uniform(-speed_variance, speed_variance)

                vx = math.cos(angle) * speed
                vy = math.sin(angle) * speed

                # Slight color variation per pixel
                color = QColor(base_color)
                h, s, v, a = color.getHsv()
                h = (h + random.randint(-20, 20)) % 360
                color = QColor.fromHsv(h, s, v)

                pixel = {
                    "x": ex + offset_x,
                    "y": ey + offset_y,
                    "vx": vx,
                    "vy": vy,
                    "size": pixel_size,
                    "color": color,
                    "alpha": 1.0,
                    "age": 0.0  # Time since spawn
                }
                pixels.append(pixel)

        # Store explosion
        explosion = {
            "pixels": pixels,
            "max_age": 2.5  # Explosions last 2.5 seconds
        }
        self.explosions.append(explosion)

        # Limit number of simultaneous explosions
        max_explosions = 8
        while len(self.explosions) > max_explosions:
            self.explosions.pop(0)

    def update(self, dt_ms, energies, sensitivity, flash_thresh):
        # Track energies for color selection
        self.low_energy = energies.get('low', 0.0) * sensitivity
        self.mid_energy = energies.get('mid', 0.0) * sensitivity
        self.high_energy = energies.get('high', 0.0) * sensitivity

        dt_sec = dt_ms / 1000.0
        w, h = self.size.width(), self.size.height()

        # Update all explosions
        for explosion in self.explosions[:]:
            for pixel in explosion["pixels"][:]:
                # Age the pixel
                pixel["age"] += dt_sec

                # Apply velocity with deceleration (friction)
                friction = 0.995  # Slow down over time
                pixel["vx"] *= friction
                pixel["vy"] *= friction

                # Move pixel
                pixel["x"] += pixel["vx"] * dt_sec
                pixel["y"] += pixel["vy"] * dt_sec

                # Fade out based on age
                age_ratio = pixel["age"] / explosion["max_age"]
                pixel["alpha"] = max(0.0, 1.0 - age_ratio)

                # Remove pixels that are too old or off-screen
                if (pixel["age"] >= explosion["max_age"] or
                    pixel["x"] < -20 or pixel["x"] > w + 20 or
                    pixel["y"] < -20 or pixel["y"] > h + 20):
                    explosion["pixels"].remove(pixel)

            # Remove explosions with no pixels left
            if not explosion["pixels"]:
                self.explosions.remove(explosion)

    def paint(self, p: QPainter, brightness: float):
        if not self.explosions:
            return

        p.save()
        p.setRenderHint(QPainter.Antialiasing, False)  # Sharp pixels

        for explosion in self.explosions:
            for pixel in explosion["pixels"]:
                color = QColor(pixel["color"])
                alpha = pixel["alpha"] * brightness
                color.setAlphaF(max(0.0, min(1.0, alpha)))

                # Draw pixel as a filled rectangle
                p.fillRect(
                    int(pixel["x"]),
                    int(pixel["y"]),
                    pixel["size"],
                    pixel["size"],
                    color
                )

        p.restore()
