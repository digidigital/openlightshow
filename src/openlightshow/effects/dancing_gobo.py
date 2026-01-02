"""
DancingGobo effect - Rotating gobo pattern with oval dots in a circular vortex design.

Behavior:
- Gobo pattern: oval-shaped dots arranged on 8 invisible "spokes" from center outward
- Ovals increase in size from inner (small) to outer (larger)
- Creates a flower-like, visually engaging vortex pattern
- Same size and movement pattern as ColorfulScanner but rotates faster
- Starts in top-left quadrant center
- On beat: Moves very fast to a random other quadrant's center
- Mids: Triggers color fade change
- Bass: Controls rotation speed (on top of already faster base rotation)
- Uses neon colors for all ovals
"""

import math
import time
import random
from PySide6.QtCore import QPointF, QSize, Qt
from PySide6.QtGui import QPainter, QColor, QPen, QBrush
from ..effect_base import Effect


class DancingGobo(Effect):
    name = "Dancing Gobo"
    effect_class = "centereffect_class03"

    # Neon colors
    NEON_COLORS = [
        QColor(255, 0, 60),    # Neon red
        QColor(255, 60, 0),    # Neon orange
        QColor(255, 255, 0),   # Neon yellow
        QColor(0, 255, 60),    # Neon green
        QColor(0, 255, 255),   # Neon cyan
        QColor(0, 60, 255),    # Neon blue
        QColor(255, 0, 255),   # Neon magenta
        QColor(255, 0, 150),   # Neon pink
    ]

    def __init__(self, size: QSize):
        super().__init__(size)
        self.rotation_angle = 0.0

        # Music reactive values
        self.bass_energy = 0.0
        self.mid_energy = 0.0
        self.high_energy = 0.0

        # Beat detection
        self.last_beat_time = 0.0

        # Color management
        self.current_color = random.choice(self.NEON_COLORS)
        self.target_color = self.current_color
        self.color_transition = 1.0  # 0.0 = current, 1.0 = target
        self.last_mid_trigger = 0.0

        # Base parameters - faster rotation than ColorfulScanner
        self.base_rotation_speed = 180.0  # Degrees per second (50% faster than ColorfulScanner's 120)

        # Gobo pattern parameters
        self.num_spokes = 8
        self.ovals_per_spoke = 5  # Number of ovals from inside to outside

        # Quadrant positioning (same as ColorfulScanner)
        self.current_quadrant = 0  # 0=top-left, 1=top-right, 2=bottom-left, 3=bottom-right
        self.target_quadrant = 0
        self.quadrant_transition = 0.0  # 0.0 = at current, 1.0 = at target

        # Current position (center of gobo)
        w, h = size.width(), size.height()
        self.current_x = w * 0.25
        self.current_y = h * 0.25
        self.target_x = self.current_x
        self.target_y = self.current_y

        # Gobo size - same as ColorfulScanner circle radius
        self.gobo_radius = h * 0.1875

    def _get_quadrant_center(self, quadrant):
        """Get the center position for a given quadrant (0-3)."""
        w, h = self.size.width(), self.size.height()

        if quadrant == 0:  # Top-left
            return (w * 0.25, h * 0.25)
        elif quadrant == 1:  # Top-right
            return (w * 0.75, h * 0.25)
        elif quadrant == 2:  # Bottom-left
            return (w * 0.25, h * 0.75)
        else:  # Bottom-right (quadrant == 3)
            return (w * 0.75, h * 0.75)

    def resize(self, size: QSize):
        """Handle window resize."""
        super().resize(size)
        h = size.height()
        self.gobo_radius = h * 0.1875
        # Update quadrant positions
        self.current_x, self.current_y = self._get_quadrant_center(self.current_quadrant)
        self.target_x, self.target_y = self._get_quadrant_center(self.target_quadrant)

    def on_beat(self):
        """Triggered on beat detection."""
        current_time = time.time() * 1000.0

        # Debounce beats (200ms)
        if current_time - self.last_beat_time < 200:
            return

        self.last_beat_time = current_time

        # Jump to a random different quadrant
        other_quadrants = [q for q in range(4) if q != self.target_quadrant]
        self.current_quadrant = self.target_quadrant
        self.target_quadrant = random.choice(other_quadrants)

        # Reset transition
        self.quadrant_transition = 0.0

        # Set new target position
        self.target_x, self.target_y = self._get_quadrant_center(self.target_quadrant)

    def update(self, dt_ms, energies, sensitivity, flash_thresh):
        """Update effect state."""
        dt_sec = dt_ms / 1000.0

        # Extract energy values
        self.bass_energy = energies.get('low', 0.0) * sensitivity
        self.mid_energy = energies.get('mid', 0.0) * sensitivity
        self.high_energy = energies.get('high', 0.0) * sensitivity

        # Update rotation - continuous, bass controls speed (on top of already faster base)
        speed_multiplier = 1.0 + self.bass_energy * 2.0
        rotation_speed = self.base_rotation_speed * speed_multiplier
        self.rotation_angle += rotation_speed * dt_sec
        self.rotation_angle = self.rotation_angle % 360.0

        # Mids trigger color fade change
        current_time = time.time() * 1000.0
        if self.mid_energy > 0.5 and (current_time - self.last_mid_trigger > 300):
            self.last_mid_trigger = current_time
            # Start color transition
            if self.color_transition >= 1.0:
                self.current_color = self.target_color
                self.target_color = random.choice(self.NEON_COLORS)
                self.color_transition = 0.0

        # Update color transition
        if self.color_transition < 1.0:
            self.color_transition += dt_sec * 2.0  # 0.5 second transition
            self.color_transition = min(1.0, self.color_transition)

        # Very fast quadrant transition (same as ColorfulScanner)
        if self.quadrant_transition < 1.0:
            self.quadrant_transition += dt_sec * 20.0  # Very fast (20x per second)
            self.quadrant_transition = min(1.0, self.quadrant_transition)

            # Smooth interpolation with easing
            t = self.quadrant_transition
            # Ease-out cubic for snappy movement
            eased_t = 1.0 - pow(1.0 - t, 3)

            # Get start position
            start_x, start_y = self._get_quadrant_center(self.current_quadrant)

            # Interpolate position
            self.current_x = start_x + (self.target_x - start_x) * eased_t
            self.current_y = start_y + (self.target_y - start_y) * eased_t

    def paint(self, p: QPainter, brightness: float):
        """Render the dancing gobo effect."""
        p.save()

        # Use current position (interpolated during quadrant transition)
        cx, cy = self.current_x, self.current_y

        # Interpolate color
        if self.color_transition < 1.0:
            # Blend between current and target color
            r1, g1, b1 = self.current_color.red(), self.current_color.green(), self.current_color.blue()
            r2, g2, b2 = self.target_color.red(), self.target_color.green(), self.target_color.blue()
            t = self.color_transition
            r = int(r1 + (r2 - r1) * t)
            g = int(g1 + (g2 - g1) * t)
            b = int(b1 + (b2 - b1) * t)
            color = QColor(r, g, b)
        else:
            color = QColor(self.target_color)

        # Apply brightness
        alpha = max(0.0, min(1.0, brightness))
        color.setAlphaF(alpha)

        # Set up painter
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(color))

        # Draw ovals on 8 spokes
        angle_per_spoke = 360.0 / self.num_spokes

        for spoke_idx in range(self.num_spokes):
            # Calculate spoke angle (with rotation)
            spoke_angle = (spoke_idx * angle_per_spoke + self.rotation_angle) % 360.0
            spoke_rad = math.radians(spoke_angle)

            # Draw ovals along this spoke from inside to outside
            for oval_idx in range(self.ovals_per_spoke):
                # Distance from center (normalized 0.0 to 1.0)
                distance_factor = (oval_idx + 1) / self.ovals_per_spoke

                # Actual distance from center
                distance = self.gobo_radius * distance_factor

                # Position of oval center
                oval_x = cx + distance * math.cos(spoke_rad)
                oval_y = cy - distance * math.sin(spoke_rad)  # Negative because y increases downward

                # Oval size increases with distance - made larger
                # Inner ovals: small, outer ovals: larger
                # Width (shorter side, parallel to spoke): 12px to 32px
                # Height (longer side, perpendicular to spoke): 20px to 50px
                oval_width = 12 + distance_factor * 20
                oval_height = 20 + distance_factor * 30

                # Save painter state for rotation
                p.save()

                # Translate to oval position
                p.translate(oval_x, oval_y)

                # Rotate to align with spoke
                # The oval's shorter side should be parallel to the spoke
                # So we rotate by the spoke angle
                p.rotate(spoke_angle)

                # Draw oval centered at origin (after translation)
                # Width is along the spoke (x-axis after rotation)
                # Height is perpendicular to spoke (y-axis after rotation)
                p.drawEllipse(
                    QPointF(0, 0),
                    oval_width / 2,   # Half-width (radial direction)
                    oval_height / 2   # Half-height (tangential direction)
                )

                # Restore painter state
                p.restore()

        p.restore()
