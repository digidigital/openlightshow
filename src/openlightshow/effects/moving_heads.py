"""
MovingHeads effect - Professional moving head light spots (projection only).

Behavior:
- Multiple independent light spots with erratic pan/tilt movement
- Spots move randomly across entire canvas
- Bass: Triggers snap movements to new random positions
- Mids: Controls movement speed
- Highs: Spot intensity and strobe effects
- Beat: Changes movement patterns and colors
"""

import math
import time
import random
from PySide6.QtCore import QPointF, QSize
from PySide6.QtGui import QPainter, QColor, QPen, QRadialGradient
from ..effect_base import Effect


class MovingBeam:
    """Represents a single moving head spot."""
    def __init__(self, index, total_beams):
        # Current position directly on screen (0 to 1 normalized)
        self.x = random.random()
        self.y = random.random()

        # Target position for movement
        self.target_x = self.x
        self.target_y = self.y

        # Color
        self.hue = random.random()
        self.target_hue = self.hue

        # Spot characteristics
        self.spot_size = random.uniform(20, 45)
        self.beam_intensity = 1.0

        # Erratic movement timing
        self.time_to_next_jump = random.uniform(0.3, 1.5)  # Seconds until next random jump
        self.jump_accumulator = 0.0

        # Strobe
        self.strobe_on = False
        self.strobe_phase = 0.0


class MovingHeadsEffect(Effect):
    name = "MovingHeads"
    effect_class = "particle_class01"

    def __init__(self, size: QSize):
        super().__init__(size)
        self.beams = []
        self.num_beams = 10  # Increased from 6 to 10 (4 additional beams)
        self._initialize_beams()

        # Music reactive values
        self.bass_energy = 0.0
        self.mid_energy = 0.0
        self.high_energy = 0.0

        # Beat detection
        self.last_beat_time = 0.0
        self.beat_sync = 0.0  # When >0, all beams move in sync
        self.beat_count = 0

    def _initialize_beams(self):
        """Create the moving beams, preserving existing beam positions."""
        # Keep existing beams and their positions
        existing_beams = self.beams[:]

        # If we need more beams, add new ones
        if len(existing_beams) < self.num_beams:
            for i in range(len(existing_beams), self.num_beams):
                new_beam = MovingBeam(i, self.num_beams)
                existing_beams.append(new_beam)

        # If we need fewer beams, remove extras
        self.beams = existing_beams[:self.num_beams]

    def on_beat(self):
        """Triggered on beat detection."""
        current_time = time.time() * 1000.0

        # Debounce beats (200ms)
        if current_time - self.last_beat_time < 200:
            return

        self.last_beat_time = current_time
        self.beat_count += 1

        # Trigger synchronized movement
        self.beat_sync = 1.0

        # Every beat, make all beams jump to new random positions
        for beam in self.beams:
            beam.target_x = random.random()
            beam.target_y = random.random()
            beam.target_hue = random.random()

        # Every 16 beats, change number of beams (8-12 range)
        if self.beat_count % 16 == 0:
            old_num = self.num_beams
            self.num_beams = random.randint(8, 12)
            if self.num_beams != old_num:
                self._initialize_beams()

    def update(self, dt_ms, energies, sensitivity, flash_thresh):
        """Update effect state."""
        dt_sec = dt_ms / 1000.0

        # Extract energy values
        self.bass_energy = energies.get('low', 0.0) * sensitivity
        self.mid_energy = energies.get('mid', 0.0) * sensitivity
        self.high_energy = energies.get('high', 0.0) * sensitivity

        # Update each beam
        for i, beam in enumerate(self.beams):
            self._update_beam(beam, i, dt_sec)

        # Decay beat sync
        if self.beat_sync > 0:
            self.beat_sync -= dt_sec * 2.0
            self.beat_sync = max(0.0, self.beat_sync)

    def _update_beam(self, beam, index, dt_sec):
        """Update a single moving beam."""
        # Erratic movement - jump to new random positions periodically
        beam.jump_accumulator += dt_sec

        if beam.jump_accumulator >= beam.time_to_next_jump:
            # Time to jump to a new random position
            beam.target_x = random.random()
            beam.target_y = random.random()
            beam.time_to_next_jump = random.uniform(0.3, 1.5)
            beam.jump_accumulator = 0.0

        # Movement speed influenced by mids - erratic and fast
        base_speed = 2.5  # Position units per second (0-1 range)
        move_speed = base_speed * (0.5 + self.mid_energy * 1.5)

        # Snap to target on strong bass (instant jump)
        if self.bass_energy > 0.7:
            beam.x = beam.target_x
            beam.y = beam.target_y
        else:
            # Move towards target with erratic speed
            x_diff = beam.target_x - beam.x
            y_diff = beam.target_y - beam.y

            beam.x += x_diff * min(1.0, move_speed * dt_sec)
            beam.y += y_diff * min(1.0, move_speed * dt_sec)

        # Clamp to screen bounds
        beam.x = max(0.0, min(1.0, beam.x))
        beam.y = max(0.0, min(1.0, beam.y))

        # Update color
        hue_diff = beam.target_hue - beam.hue
        if abs(hue_diff) > 0.5:  # Wrap around
            if hue_diff > 0:
                hue_diff -= 1.0
            else:
                hue_diff += 1.0
        beam.hue += hue_diff * min(1.0, dt_sec * 2.0)
        beam.hue = beam.hue % 1.0

        # Update beam intensity based on high energy
        beam.beam_intensity = 0.7 + self.high_energy * 0.3

        # Strobe effect
        beam.strobe_phase += dt_sec * 20.0
        beam.strobe_on = (self.high_energy > 0.8 and int(beam.strobe_phase) % 2 == 0)

    def paint(self, p: QPainter, brightness: float):
        """Render the moving head beams."""
        p.save()

        w, h = self.size.width(), self.size.height()

        # Draw beams
        for beam in self.beams:
            # Skip if strobing off
            if beam.strobe_on:
                continue

            self._draw_beam(p, beam, w, h, brightness)

        p.restore()

    def _draw_beam(self, p: QPainter, beam, screen_width, screen_height, brightness_val):
        """Draw the light spot."""
        # Convert normalized position (0-1) to screen coordinates
        beam_center_x = beam.x * screen_width
        beam_center_y = beam.y * screen_height

        # Draw spot with radial gradient
        gradient = QRadialGradient(beam_center_x, beam_center_y, beam.spot_size * 1.5)

        beam_color = QColor.fromHsvF(beam.hue, 0.8, beam.beam_intensity)
        beam_alpha = max(0.0, min(1.0, brightness_val * 0.6))
        beam_color.setAlphaF(beam_alpha)

        transparent = QColor.fromHsvF(beam.hue, 0.6, 0.5)
        transparent.setAlphaF(0.0)

        gradient.setColorAt(0.0, beam_color)
        gradient.setColorAt(0.6, transparent)
        gradient.setColorAt(1.0, transparent)

        p.setPen(QPen(QColor(0, 0, 0, 0)))
        p.setBrush(gradient)
        p.drawEllipse(QPointF(beam_center_x, beam_center_y), beam.spot_size * 1.5, beam.spot_size * 1.5)

        # Draw brighter center
        center_color = QColor.fromHsvF(beam.hue, 0.6, 1.0)
        center_alpha = max(0.0, min(1.0, brightness_val * 0.8))
        center_color.setAlphaF(center_alpha)
        p.setBrush(center_color)
        p.drawEllipse(QPointF(beam_center_x, beam_center_y), beam.spot_size * 0.6, beam.spot_size * 0.6)
