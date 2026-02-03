from PySide6.QtCore import QSize, QPointF
from PySide6.QtGui import QPainter, QColor, QPen
from ..effect_base import Effect
import random
import time


class TechnoFlasher(Effect):
    """
    TechnoFlasher effect:
    - Beats fire many short bright neon lines (4px wide)
    - Lines are symmetrically mirrored on screen center
    - Mids fire flashing/strobing discs (10px diameter)
    - All positions are random
    - Fast strobe patterns
    - Painter state is isolated with save/restore
    """
    name = "TechnoFlasher"
    effect_class = "flash_class01"

    def __init__(self, size: QSize):
        super().__init__(size)
        self.size = size

        # Line properties (triggered by beats)
        self.line_width = 8
        self.line_length = 500  # 5x longer (100 * 5 = 500)
        self.lines = []  # List of active lines: {'x', 'y', 'angle', 'color', 'lifetime', 'vx', 'vy'}

        # Disc properties (triggered by mids)
        self.disc_radius = 5  
        self.discs = []  # List of active discs: {'x', 'y', 'color', 'lifetime', 'flash_phase'}

        # Flash durations (ms)
        self.line_duration = 350  # Lines flash with double strobe (3x longer: 100 * 3 = 300)
        self.disc_duration = 300  # Discs flash and strobe (2x longer: 150 * 2 = 300)

        # Beat tracking
        self.last_beat_time = -1000
        self.beat_cooldown_ms = 200  # 200ms debounce
        self.beat_counter = 0  # Count beats for screen flash

        # Full screen flash (double flash with delay)
        self.screen_flash_active = False
        self.screen_flash_start = 0
        self.screen_flash_duration = 50  # 80ms per flash
        self.screen_flash_delay = 80  # 100ms (0.1s) delay between flashes
        self.screen_flash_count = 0  # Track which flash (0 or 1)

        # Mid tracking
        self.last_mid_trigger = -1000
        self.mid_cooldown_ms = 150  # 150ms between mid triggers
        self.mid_threshold = 0.4  # Threshold for mid energy

        # Number of elements to spawn
        self.lines_per_beat = 3  # lines 
        self.discs_per_mid = 10  # Multiple discs per mid trigger (half of 16)

        # Line movement speed (pixels per second)
        self.line_speed = 800.0

        # Neon colors
        self.neon_colors = [
            QColor(57, 255, 20),    # neon green
            QColor(255, 20, 147),   # neon pink
            QColor(100, 255, 255),    # neon cyan
            QColor(255, 255, 100),    # neon yellow
            QColor(255, 100, 255),    # neon magenta
            QColor(255, 165, 100),    # neon orange
            QColor(100, 255, 128),    # neon lime
            QColor(255, 50, 255),   # bright purple
            QColor(255, 100, 100),  # bright red
            QColor(100, 255, 255),  # bright cyan
            QColor(255, 255, 100),  # bright yellow
        ]

    def resize(self, size: QSize):
        super().resize(size)
        self.size = size

    def on_beat(self):
        """Trigger line flashes on beat."""
        super().on_beat()
        now = time.time() * 1000
        if now - self.last_beat_time >= self.beat_cooldown_ms:
            self.last_beat_time = now
            self.beat_counter += 1

            # Trigger screen flash every 2 beats (changed from 4)
            if self.beat_counter % 2 == 0:
                self.screen_flash_active = True
                self.screen_flash_start = now
                self.screen_flash_count = 0  # Reset to first flash

            self._spawn_lines()

    def _spawn_lines(self):
        """Spawn symmetrically mirrored short lines."""
        center_x = self.size.width() / 2
        center_y = self.size.height() / 2

        for _ in range(self.lines_per_beat):
            # Random position on left half
            x = random.uniform(0, center_x)
            y = random.uniform(0, self.size.height())

            # Random angle
            angle = random.uniform(0, 2 * 3.14159)

            # Random neon color
            color = random.choice(self.neon_colors)

            # Random velocity for movement
            vel_angle = random.uniform(0, 2 * 3.14159)
            vx = random.uniform(0.5, 1.5) * self.line_speed * 3.14159 / 180 * 57.2958 * 0.1
            vy = random.uniform(0.5, 1.5) * self.line_speed * 3.14159 / 180 * 57.2958 * 0.1
            import math
            vx = math.cos(vel_angle) * self.line_speed
            vy = math.sin(vel_angle) * self.line_speed

            # Create line on left side
            line_left = {
                'x': x,
                'y': y,
                'angle': angle,
                'color': color,
                'lifetime': 0,
                'vx': vx,
                'vy': vy
            }
            self.lines.append(line_left)

            # Create mirrored line on right side (mirror velocity too)
            line_right = {
                'x': self.size.width() - x,  # Mirror X position
                'y': y,
                'angle': 3.14159 - angle,  # Mirror angle
                'color': color,
                'lifetime': 0,
                'vx': -vx,  # Mirror X velocity
                'vy': vy   # Keep Y velocity same
            }
            self.lines.append(line_right)

    def _spawn_discs(self):
        """Spawn random strobing discs."""
        now = time.time() * 1000
        if now - self.last_mid_trigger >= self.mid_cooldown_ms:
            self.last_mid_trigger = now

            for _ in range(self.discs_per_mid):
                # Random position anywhere on screen
                x = random.uniform(self.disc_radius, self.size.width() - self.disc_radius)
                y = random.uniform(self.disc_radius, self.size.height() - self.disc_radius)

                # Random neon color
                color = random.choice(self.neon_colors)

                # Random flash phase offset for strobe effect
                flash_phase = random.uniform(0, 1)

                disc = {
                    'x': x,
                    'y': y,
                    'color': color,
                    'lifetime': 0,
                    'flash_phase': flash_phase
                }
                self.discs.append(disc)

    def update(self, dt_ms: int, energies: dict, sensitivity: float, flash_thresh: float):
        """Update flash lifetimes and trigger on mid energy."""
        dt_sec = dt_ms / 1000.0

        # Check mid energy for disc spawning
        mid = energies.get('mid', 0.0) * sensitivity
        if mid > self.mid_threshold:
            self._spawn_discs()

        # Update screen flash state (double flash with delay)
        if self.screen_flash_active:
            now = time.time() * 1000
            elapsed = now - self.screen_flash_start

            if self.screen_flash_count == 0:
                # First flash
                if elapsed >= self.screen_flash_duration:
                    # First flash done, wait for delay
                    if elapsed >= self.screen_flash_duration + self.screen_flash_delay:
                        # Start second flash
                        self.screen_flash_count = 1
            else:
                # Second flash
                total_elapsed = elapsed - self.screen_flash_duration - self.screen_flash_delay
                if total_elapsed >= self.screen_flash_duration:
                    # Both flashes done
                    self.screen_flash_active = False

        # Update line lifetimes and positions
        lines_to_remove = []
        for i, line in enumerate(self.lines):
            line['lifetime'] += dt_ms

            # Update position based on velocity
            line['x'] += line['vx'] * dt_sec
            line['y'] += line['vy'] * dt_sec

            if line['lifetime'] >= self.line_duration:
                lines_to_remove.append(i)

        # Remove expired lines
        for i in reversed(lines_to_remove):
            self.lines.pop(i)

        # Update disc lifetimes
        discs_to_remove = []
        for i, disc in enumerate(self.discs):
            disc['lifetime'] += dt_ms
            if disc['lifetime'] >= self.disc_duration:
                discs_to_remove.append(i)

        # Remove expired discs
        for i in reversed(discs_to_remove):
            self.discs.pop(i)

    def paint(self, painter: QPainter, brightness: float):
        """Draw the TechnoFlasher effect."""
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)

        import math

        # Draw full screen double flash every 2 beats
        if self.screen_flash_active:
            now = time.time() * 1000
            elapsed = now - self.screen_flash_start

            # Determine if we should show flash based on timing
            show_flash = False
            if self.screen_flash_count == 0:
                # First flash period
                if elapsed < self.screen_flash_duration:
                    show_flash = True
            else:
                # Second flash period (after delay)
                total_elapsed = elapsed - self.screen_flash_duration - self.screen_flash_delay
                if total_elapsed < self.screen_flash_duration:
                    show_flash = True

            if show_flash:
                flash_color = QColor(255, 255, 255)
                flash_color.setAlphaF(brightness * 0.64)  # 64% opacity white flash (20% darker than 80%)
                painter.fillRect(0, 0, self.size.width(), self.size.height(), flash_color)

        # Draw lines with double strobe effect
        for line in self.lines:
            # Calculate line endpoints
            angle = line['angle']
            half_length = self.line_length / 2

            dx = math.cos(angle) * half_length
            dy = math.sin(angle) * half_length

            x1 = line['x'] - dx
            y1 = line['y'] - dy
            x2 = line['x'] + dx
            y2 = line['y'] + dy

            # Double strobe: flash on/off twice during lifetime
            progress = line['lifetime'] / self.line_duration
            strobe_cycle = (progress * 4.0) % 1.0  # 4 cycles = 2 on, 2 off

            # Only draw if in "on" phase (first and third quarter)
            if strobe_cycle < 0.5:
                # Color with fade based on lifetime
                color = QColor(line['color'])
                alpha = brightness * (1.0 - progress)
                color.setAlphaF(max(0.0, min(1.0, alpha)))

                pen = QPen(color, self.line_width)
                painter.setPen(pen)
                painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))

                # Draw white discs at line endpoints (same diameter as line width)
                white_color = QColor(255, 255, 255)
                white_color.setAlphaF(max(0.0, min(1.0, alpha)))
                painter.setBrush(white_color)
                painter.setPen(QColor(0, 0, 0, 0))  # No outline

                disc_radius = self.line_width / 2
                painter.drawEllipse(QPointF(x1, y1), disc_radius, disc_radius)
                painter.drawEllipse(QPointF(x2, y2), disc_radius, disc_radius)

        # Draw discs with strobe effect
        painter.setPen(QColor(0, 0, 0, 0))  # No outline
        for disc in self.discs:
            # Strobe effect: flash on/off rapidly
            progress = disc['lifetime'] / self.disc_duration
            strobe_frequency = 10.0  # Hz
            strobe_phase = (progress * strobe_frequency + disc['flash_phase']) % 1.0

            # Only draw if in "on" phase of strobe
            if strobe_phase < 0.5:
                color = QColor(disc['color'])
                # Fade out over lifetime - much brighter
                alpha = brightness * (1.0 - progress * 0.5) * 2.0
                color.setAlphaF(max(0.0, min(1.0, alpha)))

                painter.setBrush(color)
                painter.drawEllipse(
                    QPointF(disc['x'], disc['y']),
                    self.disc_radius,
                    self.disc_radius
                )

        painter.restore()
