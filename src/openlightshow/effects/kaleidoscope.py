import math
import time
import random
from PySide6.QtCore import QSize, QPointF, Qt
from PySide6.QtGui import QPainter, QColor, QPen, QBrush
from ..effect_base import Effect


class Kaleidoscope(Effect):
    """
    Kaleidoscope Effect:
    - Spawns ONE shape per beat at center (max size: 1/10 screen height)
    - Shapes travel toward screen borders and leave the screen
    - Random bright neon colors per shape
    - Mids change individual shape colors
    - Works in top-left quadrant only, mirrored to other 3 quadrants
    - Shapes stay within quadrant bounds to prevent intersection at borders
    - 170ms beat debounce
    """

    name = "Kaleidoscope"
    effect_class = "effect_class22"

    def __init__(self, size: QSize):
        super().__init__(size)
        self.shapes = []  # list of dicts: {"x", "y", "vx", "vy", "size", "color", "type", "hue_shift", "rotation"}

        # Beat debounce
        self.last_beat_time = 0.0
        self.beat_debounce_ms = 200

        # Mid energy for color shifting
        self.mid_energy = 0.0

        # Speed multiplier (3x)
        self.speed_multiplier = 3

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
        ]

    def on_beat(self):
        # Debounce: ignore beats too close together - spawn ONLY on beats
        now = time.time() * 200.0
        if now - self.last_beat_time < self.beat_debounce_ms:
            return
        self.last_beat_time = now

        super().on_beat()

        # Spawn exactly ONE shape per beat at center
        w, h = self.size.width(), self.size.height()
        max_size = h / 5.0

        # Random size up to max
        size = random.uniform(max_size * 0.2, max_size)

        # Spawn at center
        cx, cy = w / 2, h / 2

        # Random velocity pointing toward top-left quadrant
        # Apply 3x speed multiplier
        base_speed = random.uniform(70, 250)
        speed = base_speed * self.speed_multiplier
        # Angle range for top-left quadrant, avoiding the exact axes (borders)
        # Use range [225°-270°] = [1.25π - 1.5π] to stay away from borders
        angle = random.uniform(1.1 * math.pi, 1.5 * math.pi)
        vx = math.cos(angle) * speed
        vy = math.sin(angle) * speed

        # Random shape type (0=circle, 1=square, 2=triangle)
        shape_type = random.randint(0, 2)

        # Random rotation speed (radians per second)
        # Some shapes rotate clockwise, some counter-clockwise
        rotation_speed = random.uniform(-2.0, 2.0)  # -2 to +2 rad/s

        new_shape = {
            "x": cx,
            "y": cy,
            "vx": vx,
            "vy": vy,
            "size": size,
            "color": random.choice(self.neon_colors),
            "type": shape_type,
            "hue_shift": 0.0,
            "rotation": 0.0,
            "rotation_speed": rotation_speed
        }
        self.shapes.append(new_shape)

        # Limit total shapes (fewer since we only spawn 1 per beat)
        max_shapes = 12
        while len(self.shapes) > max_shapes:
            self.shapes.pop(0)

    def update(self, dt_ms, energies, sensitivity, flash_thresh):
        # Track mid energy for color shifting
        self.mid_energy = energies.get('mid', 0.0) * sensitivity

        dt_sec = dt_ms / 1000.0
        w, h = self.size.width(), self.size.height()

        # Update all shapes
        for shape in self.shapes[:]:
            # Move shape
            shape["x"] += shape["vx"] * dt_sec
            shape["y"] += shape["vy"] * dt_sec

            # Rotate shape
            shape["rotation"] += shape["rotation_speed"] * dt_sec
            shape["rotation"] %= (2 * math.pi)

            # Color shift based on mids
            shape["hue_shift"] += self.mid_energy * dt_sec * 360.0
            shape["hue_shift"] %= 360.0

            # Remove shapes that left the screen (in all quadrants)
            # Since we mirror, we need to check if it's outside in any direction
            if (shape["x"] < -shape["size"] or shape["x"] > w + shape["size"] or
                shape["y"] < -shape["size"] or shape["y"] > h + shape["size"]):
                self.shapes.remove(shape)

    def paint(self, p: QPainter, brightness: float):
        if not self.shapes:
            return

        p.save()
        p.setRenderHint(QPainter.Antialiasing, True)

        w, h = self.size.width(), self.size.height()
        cx, cy = w / 2, h / 2

        for shape in self.shapes:
            # Get base color and apply hue shift
            base_color = QColor(shape["color"])
            h_val, s_val, v_val, a_val = base_color.getHsv()
            h_val = (h_val + int(shape["hue_shift"])) % 360
            color = QColor.fromHsv(h_val, s_val, v_val)
            color.setAlphaF(max(0.0, min(1.0, brightness)))

            # Calculate position relative to center
            dx = shape["x"] - cx
            dy = shape["y"] - cy

            size = shape["size"]
            shape_type = shape["type"]

            # To avoid intersection at quadrant borders, we add a small offset
            # This ensures shapes don't overlap when mirrored
            border_margin = 2.0  # Small gap at borders

            # Draw in all 4 quadrants (mirror effect)
            # Only draw if the shape is not too close to the center axes
            positions = [
                (cx + dx, cy + dy),  # Top-right / original
                (cx - dx, cy + dy),  # Top-left (mirrored horizontally)
                (cx + dx, cy - dy),  # Bottom-right (mirrored vertically)
                (cx - dx, cy - dy),  # Bottom-left (mirrored both)
            ]

            for px, py in positions:
                # Skip drawing if shape would overlap with quadrant borders
                # (when shape center is too close to center axes)
                if abs(px - cx) < size / 2 + border_margin or abs(py - cy) < size / 2 + border_margin:
                    continue

                # Apply rotation transform
                p.save()
                p.translate(px, py)
                p.rotate(math.degrees(shape["rotation"]))

                if shape_type == 0:  # Circle (rotation doesn't visually affect circles, but included for consistency)
                    p.setPen(QPen(color, 2))
                    p.setBrush(Qt.NoBrush)
                    p.drawEllipse(QPointF(0, 0), size / 2, size / 2)
                elif shape_type == 1:  # Square
                    p.setPen(QPen(color, 2))
                    p.setBrush(Qt.NoBrush)
                    p.drawRect(int(-size / 2), int(-size / 2), int(size), int(size))
                elif shape_type == 2:  # Triangle
                    p.setPen(QPen(color, 2))
                    p.setBrush(Qt.NoBrush)
                    half = size / 2
                    points = [
                        QPointF(0, -half),           # Top
                        QPointF(-half, half),        # Bottom left
                        QPointF(half, half),         # Bottom right
                    ]
                    from PySide6.QtGui import QPolygonF
                    p.drawPolygon(QPolygonF(points))

                p.restore()

        p.restore()
