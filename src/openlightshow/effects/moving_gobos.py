"""
MovingGobos effect - Two independently moving gobo patterns that bounce off walls.

Behavior:
- Two gobo patterns (oval dots on spokes) move fluidly across the screen
- Each gobo bounces off screen edges like a Pong ball
- Gobos start at screen center at random angles (minimum 90 degrees apart)
- BPM controls traveling speed (default 120 BPM until measured)
- Each gobo changes color independently
- Bass: Triggers color changes
- Mids: Affects rotation speed
- Beat: Triggers color changes and slight speed boost
"""

import math
import time
import random
from PySide6.QtCore import QPointF, QSize, Qt
from PySide6.QtGui import QPainter, QColor, QPen, QBrush
from ..effect_base import Effect


class Gobo:
    """A single moving gobo pattern."""

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

    def __init__(self, x, y, angle, gobo_radius, rotation_direction):
        self.x = x
        self.y = y
        self.angle = angle  # Direction of movement in degrees
        self.speed = 0.0  # Pixels per second, will be set by BPM
        self.gobo_radius = gobo_radius
        self.rotation_angle = random.uniform(0, 360)
        self.rotation_direction = rotation_direction  # 1 for clockwise, -1 for counter-clockwise

        # Color management
        self.current_color = random.choice(self.NEON_COLORS)
        self.target_color = self.current_color
        self.color_transition = 1.0  # 0.0 = current, 1.0 = target

        # Gobo pattern parameters
        self.num_spokes = 8
        self.ovals_per_spoke = 5

    def trigger_color_change(self):
        """Trigger a color change."""
        if self.color_transition >= 1.0:
            self.current_color = self.target_color
            self.target_color = random.choice(self.NEON_COLORS)
            self.color_transition = 0.0

    def update_color_transition(self, dt_sec):
        """Update color transition."""
        if self.color_transition < 1.0:
            self.color_transition += dt_sec * 2.0  # 0.5 second transition
            self.color_transition = min(1.0, self.color_transition)

    def get_color(self):
        """Get the current interpolated color."""
        if self.color_transition < 1.0:
            # Blend between current and target color
            r1, g1, b1 = self.current_color.red(), self.current_color.green(), self.current_color.blue()
            r2, g2, b2 = self.target_color.red(), self.target_color.green(), self.target_color.blue()
            t = self.color_transition
            r = int(r1 + (r2 - r1) * t)
            g = int(g1 + (g2 - g1) * t)
            b = int(b1 + (b2 - b1) * t)
            return QColor(r, g, b)
        else:
            return QColor(self.target_color)


class MovingGobos(Effect):
    name = "MovingGobos"
    effect_class = "centereffect_class03"

    def __init__(self, size: QSize):
        super().__init__(size)

        # Music reactive values
        self.bass_energy = 0.0
        self.mid_energy = 0.0
        self.high_energy = 0.0

        # Beat detection
        self.last_beat_time = 0.0
        self.last_bass_trigger = [0.0, 0.0]  # For each gobo

        # BPM parameters
        self.bpm = 120.0  # Default BPM
        self.base_speed = 1000.0  # Base pixels per second at 120 BPM (5x faster)

        # Gobo size
        h = size.height()
        gobo_radius = h * 0.1875

        # Initialize two gobos at screen center with different angles
        w, h = size.width(), size.height()
        cx, cy = w / 2, h / 2

        # Random starting angle for first gobo
        angle1 = random.uniform(0, 360)

        # Second gobo starts at least 90 degrees away
        angle2 = angle1 + random.uniform(90, 270)
        angle2 = angle2 % 360

        self.gobos = [
            Gobo(cx, cy, angle1, gobo_radius, rotation_direction=1),   # Clockwise
            Gobo(cx, cy, angle2, gobo_radius, rotation_direction=-1)   # Counter-clockwise
        ]

        # Set initial speed based on default BPM
        self._update_speeds()

        # Base rotation speed (affected by mids)
        self.base_rotation_speed = 180.0  # Degrees per second

    def _update_speeds(self):
        """Update gobo speeds based on current BPM."""
        # Speed scales with BPM: at 120 BPM = base_speed, at 240 BPM = 2x base_speed
        speed = self.base_speed * (self.bpm / 120.0)
        for gobo in self.gobos:
            gobo.speed = speed

    def resize(self, size: QSize):
        """Handle window resize."""
        super().resize(size)
        w, h = size.width(), size.height()
        cx, cy = w / 2, h / 2
        gobo_radius = h * 0.1875

        # Update gobo radius and reposition to center
        for gobo in self.gobos:
            gobo.gobo_radius = gobo_radius
            gobo.x = cx
            gobo.y = cy

    def on_beat(self):
        """Triggered on beat detection."""
        current_time = time.time() * 1000.0

        # Debounce beats (200ms)
        if current_time - self.last_beat_time < 200:
            return

        self.last_beat_time = current_time

        # Trigger color change for both gobos
        for gobo in self.gobos:
            gobo.trigger_color_change()

        # Update BPM estimate if available
        if hasattr(self, 'bpm_estimate') and self.bpm_estimate > 0:
            self.bpm = self.bpm_estimate
            self._update_speeds()

    def update(self, dt_ms, energies, sensitivity, flash_thresh):
        """Update effect state."""
        dt_sec = dt_ms / 1000.0

        # Extract energy values
        self.bass_energy = energies.get('low', 0.0) * sensitivity
        self.mid_energy = energies.get('mid', 0.0) * sensitivity
        self.high_energy = energies.get('high', 0.0) * sensitivity

        # Bass triggers independent color changes for each gobo
        current_time = time.time() * 1000.0
        for i, gobo in enumerate(self.gobos):
            if self.bass_energy > 0.6 and (current_time - self.last_bass_trigger[i] > 400):
                self.last_bass_trigger[i] = current_time
                gobo.trigger_color_change()

        # Update each gobo
        w, h = self.size.width(), self.size.height()

        for gobo in self.gobos:
            # Update color transition
            gobo.update_color_transition(dt_sec)

            # Update rotation - mids affect rotation speed, direction is per-gobo
            speed_multiplier = 1.0 + self.mid_energy * 1.5
            rotation_speed = self.base_rotation_speed * speed_multiplier * gobo.rotation_direction
            gobo.rotation_angle += rotation_speed * dt_sec
            gobo.rotation_angle = gobo.rotation_angle % 360.0

            # Calculate movement with fluid speed (no abrupt changes)
            angle_rad = math.radians(gobo.angle)
            dx = math.cos(angle_rad) * gobo.speed * dt_sec
            dy = -math.sin(angle_rad) * gobo.speed * dt_sec  # Negative because y increases downward

            # Update position
            new_x = gobo.x + dx
            new_y = gobo.y + dy

            # Check for wall collisions and bounce
            margin = gobo.gobo_radius  # Keep gobo fully on screen

            # Bounce off left/right walls
            if new_x - margin < 0:
                new_x = margin
                gobo.angle = 180 - gobo.angle
                gobo.angle = gobo.angle % 360
            elif new_x + margin > w:
                new_x = w - margin
                gobo.angle = 180 - gobo.angle
                gobo.angle = gobo.angle % 360

            # Bounce off top/bottom walls
            if new_y - margin < 0:
                new_y = margin
                gobo.angle = -gobo.angle
                gobo.angle = gobo.angle % 360
            elif new_y + margin > h:
                new_y = h - margin
                gobo.angle = -gobo.angle
                gobo.angle = gobo.angle % 360

            gobo.x = new_x
            gobo.y = new_y

        # Check for gobo-to-gobo collisions
        if len(self.gobos) == 2:
            gobo1, gobo2 = self.gobos[0], self.gobos[1]

            # Calculate distance between gobo centers
            dx = gobo2.x - gobo1.x
            dy = gobo2.y - gobo1.y
            distance = math.sqrt(dx * dx + dy * dy)

            # Collision threshold: sum of their radii
            collision_distance = gobo1.gobo_radius + gobo2.gobo_radius

            if distance < collision_distance and distance > 0:
                # Gobos are colliding - calculate bounce angles
                # Find the collision normal (direction from gobo1 to gobo2)
                normal_x = dx / distance
                normal_y = dy / distance

                # Calculate relative velocity
                angle1_rad = math.radians(gobo1.angle)
                angle2_rad = math.radians(gobo2.angle)
                v1x = math.cos(angle1_rad) * gobo1.speed
                v1y = -math.sin(angle1_rad) * gobo1.speed
                v2x = math.cos(angle2_rad) * gobo2.speed
                v2y = -math.sin(angle2_rad) * gobo2.speed

                # Relative velocity along collision normal
                rel_vel = (v1x - v2x) * normal_x + (v1y - v2y) * normal_y

                # Only process if gobos are moving towards each other
                if rel_vel > 0:
                    # Reflect velocities (elastic collision, equal mass)
                    # Exchange velocity components along the collision normal
                    v1x_new = v1x - rel_vel * normal_x
                    v1y_new = v1y - rel_vel * normal_y
                    v2x_new = v2x + rel_vel * normal_x
                    v2y_new = v2y + rel_vel * normal_y

                    # Convert back to angle for gobo1
                    gobo1.angle = math.degrees(math.atan2(-v1y_new, v1x_new)) % 360

                    # Convert back to angle for gobo2
                    gobo2.angle = math.degrees(math.atan2(-v2y_new, v2x_new)) % 360

                    # Separate gobos to avoid overlap
                    overlap = collision_distance - distance
                    separation = overlap / 2 + 1  # Add small buffer
                    gobo1.x -= normal_x * separation
                    gobo1.y -= normal_y * separation
                    gobo2.x += normal_x * separation
                    gobo2.y += normal_y * separation

    def paint(self, p: QPainter, brightness: float):
        """Render the moving gobos."""
        if brightness <= 0:
            return

        p.save()

        # Draw each gobo
        for gobo in self.gobos:
            self._draw_gobo(p, gobo, brightness)

        p.restore()

    def _draw_gobo(self, p: QPainter, gobo, brightness):
        """Draw a single gobo pattern."""
        cx, cy = gobo.x, gobo.y

        # Get interpolated color
        color = gobo.get_color()

        # Apply brightness
        alpha = max(0.0, min(1.0, brightness))
        color.setAlphaF(alpha)

        # Set up painter
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(color))

        # Draw ovals on 8 spokes
        angle_per_spoke = 360.0 / gobo.num_spokes

        for spoke_idx in range(gobo.num_spokes):
            # Calculate spoke angle (with rotation)
            spoke_angle = (spoke_idx * angle_per_spoke + gobo.rotation_angle) % 360.0
            spoke_rad = math.radians(spoke_angle)

            # Draw ovals along this spoke from inside to outside
            for oval_idx in range(gobo.ovals_per_spoke):
                # Distance from center (normalized 0.0 to 1.0)
                distance_factor = (oval_idx + 1) / gobo.ovals_per_spoke

                # Actual distance from center
                distance = gobo.gobo_radius * distance_factor

                # Position of oval center
                oval_x = cx + distance * math.cos(spoke_rad)
                oval_y = cy - distance * math.sin(spoke_rad)  # Negative because y increases downward

                # Oval size increases with distance
                oval_width = 12 + distance_factor * 20
                oval_height = 20 + distance_factor * 30

                # Save painter state for rotation
                p.save()

                # Translate to oval position
                p.translate(oval_x, oval_y)

                # Rotate to align with spoke
                p.rotate(spoke_angle)

                # Draw oval centered at origin (after translation)
                p.drawEllipse(
                    QPointF(0, 0),
                    oval_width / 2,   # Half-width (radial direction)
                    oval_height / 2   # Half-height (tangential direction)
                )

                # Restore painter state
                p.restore()
