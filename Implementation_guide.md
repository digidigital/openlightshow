# 🎨 OpenLightShow - Developer Guide

This application uses a **fully modular plugin-based architecture**. You can add new visual effects without modifying the main application code!

## 🏗️ Architecture Overview

The application automatically discovers and loads effects from the `effects/` directory. Here's how it works:

```
openlightshow/
├── src/
│   └── openlightshow/
│       ├── main.py              # Main application (no effect code!)
│       ├── effect_base.py       # Base Effect class
│       ├── effect_loader.py     # Auto-discovery system
│       ├── presets.toml         # Preset configurations
│       ├── exclude_list.toml    # Effect conflict rules
│       ├── icons/               # Application icons
│       └── effects/             # Plugin directory
│           ├── __init__.py
│           ├── bullet_holes.py  # Self-contained effect
│           ├── moving_gobos.py  # Self-contained effect
│           └── ... (50+ effects)
├── pyproject.toml              # Package configuration
└── README.md                   # Project documentation
```

## ✨ Adding a New Effect (Simple 3-Step Process)

### Step 1: Create Your Effect File

Create a new `.py` file in the `src/openlightshow/effects/` directory (e.g., `src/openlightshow/effects/my_awesome_effect.py`):

```python
import random
import math
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QPainter, QColor, QPen
from ..effect_base import Effect


class MyAwesomeEffect(Effect):
    """
    Brief description of what your effect does.
    """

    name = "My Awesome Effect"  # This will appear in the UI
    effect_class = "effect_class1"  # Classification for exclusion grouping

    def __init__(self, size: QSize):
        super().__init__(size)
        # Initialize your effect state here
        self.angle = 0.0

    def on_beat(self):
        """Called when a beat is detected."""
        super().on_beat()  # This randomizes self.color
        # Add beat-reactive behavior here

    def update(self, dt_ms: int, energies: dict, sensitivity: float, flash_thresh: float):
        """Called every frame (~60 FPS)."""
        # Update animation state
        # energies contains: 'low', 'mid', 'high' (0.0-1.0)
        self.angle += (dt_ms / 1000.0) * energies.get('high', 0.0) * sensitivity

    def paint(self, p: QPainter, brightness: float):
        """Render your effect."""
        p.save()

        # Your drawing code here
        w, h = self.size.width(), self.size.height()
        cx, cy = w / 2, h / 2

        color = QColor(self.color)
        color.setAlphaF(brightness)
        p.setPen(QPen(color, 3))
        p.drawLine(int(cx), int(cy), int(cx + 100), int(cy))

        p.restore()
```

### Step 2: That's It!

No, seriously. Just save the file and restart the application. Your effect will:
- ✅ Be automatically discovered
- ✅ Appear in the effects list
- ✅ Be available for selection
- ✅ Work with all existing features (weights, exclusion groups, presets)

### Step 3 (Optional): Test Your Effect

Run the application to see your effect in action:

```bash
# For development install
source venv/bin/activate  # On Linux/Mac
# or
venv\Scripts\activate     # On Windows

openlightshow

# Or if installed from PyPI
pip install openlightshow
openlightshow
```

## 📋 Effect Template with AI Assistant

If you want to use an AI assistant (like Claude, ChatGPT, or GitHub Copilot) to generate effects, use this prompt:

---

**Complete Prompt for AI:**

```
You are extending a PySide6 (version 6.9.3) music-reactive lightshow application.

Context:
- The app has a base class `Effect` in `effect_base.py`:

  class Effect:
      name: str
      effect_class: str
      def __init__(self, size: QSize): ...
      def resize(self, size: QSize): ...
      def on_beat(self): ...
      def update(self, dt_ms: int, energies: Dict[str,float], sensitivity: float, flash_thresh: float): ...
      def paint(self, p: QPainter, brightness: float): ...

- Each effect is a subclass of `Effect` with a unique `name` string and an `effect_class` attribute for grouping.
- Lifecycle:
  - `on_beat()` is called when a beat is detected.
  - `update()` is called every frame (~60 FPS) with:
    - `dt_ms`: elapsed time in milliseconds
    - `energies`: dict with normalized 'low', 'mid', 'high' frequency bands (0.0-1.0)
    - `sensitivity`: user-controlled multiplier
    - `flash_thresh`: threshold for high-frequency strobe triggers
  - `paint()` is called to render the effect using a `QPainter`.
    - the method calls p.save() at the beginning
    - the method calls p.restore() at the end
- The app automatically discovers effects from the effects/ directory.
- Constraints:
  - At most 3 effects are active at once.
  - When no music is playing, the lightshow area is black.

Your task:
- Implement a **new effect** as a subclass of `Effect` in a standalone file.
- Give it a descriptive `name` string.
- Assign an `effect_class` string (use a unique class like "effect_class43" or group with similar effects).
- Define its behavior in `on_beat`, `update`, and `paint`.
- Use `QPainter` drawing primitives (lines, rects, ellipses, arcs, fillRect, drawPoint, etc.).
- Ensure it respects the screen size (`self.size`) and stays within bounds.
- Make it visually distinct from existing effects.
- Drive visuals with `energies['low']`, `energies['mid']`, `energies['high']` and/or beats.
- Keep the background black (do not fill the entire screen except for intentional flashes).

Required imports:
```python
from ..effect_base import Effect
from PySide6.QtCore import QSize
from PySide6.QtGui import QPainter, QColor
# Add other imports as needed (QPen, random, math, etc.)
```

Output format:
- Provide the complete Python file content for the new effect.
- Include a docstring describing what the effect does.
- Save it as `src/openlightshow/effects/effect_name.py` (snake_case filename).
```

**Then describe your effect idea:**
> "Create an effect called SpiralWave: a spiral of dots that expands and contracts with the bass, rotates with mid frequencies, and changes color on beats."

---

## 🎯 Available Methods & Properties

### Base Effect Class (`effect_base.Effect`)

**Attributes:**
- `name` (str): Effect name shown in UI (must be unique)
- `effect_class` (str): Classification attribute for grouping similar effects (prevents conflicts)
- `size` (QSize): Current rendering area size
- `color` (QColor): Current effect color (randomized on beats by default)

**Methods:**
- `__init__(self, size: QSize)`: Initialize effect
- `resize(self, size: QSize)`: Handle window resize
- `on_beat(self)`: React to detected beats (default: randomize color)
- `update(self, dt_ms, energies, sensitivity, flash_thresh)`: Update animation state
- `paint(self, p: QPainter, brightness: float)`: Render the effect

### Update Method Parameters

```python
def update(self, dt_ms: int, energies: Dict[str, float], sensitivity: float, flash_thresh: float):
    pass
```

- **dt_ms**: Milliseconds since last frame
- **energies**: `{'low': 0.0-1.0, 'mid': 0.0-1.0, 'high': 0.0-1.0}`
  - `low`: Bass frequencies (20-200 Hz)
  - `mid`: Mid frequencies (200-2000 Hz)
  - `high`: Treble frequencies (2000-8000 Hz)
- **sensitivity**: User-controlled multiplier (0.0-2.0+)
- **flash_thresh**: Threshold for strobe detection (0.0-1.0)

## 🎨 QPainter Drawing Primitives

Common drawing methods you can use in `paint()`:

```python
# Lines
p.drawLine(x1, y1, x2, y2)
p.drawPolyline(QPolygonF([point1, point2, ...]))

# Shapes
p.drawRect(x, y, width, height)
p.drawEllipse(center: QPointF, rx, ry)
p.drawPolygon(QPolygonF([...]))
p.drawArc(rect, startAngle, spanAngle)

# Filled shapes
p.fillRect(x, y, width, height, color)

# Points
p.drawPoint(x, y)
p.drawPoints([QPointF(...), ...])

# Styling
p.setPen(QPen(color, width))
p.setBrush(QBrush(color))
p.setCompositionMode(QPainter.CompositionMode_Plus)  # Additive blending
p.setRenderHint(QPainter.Antialiasing, True)
```

## 📚 Examples from Existing Effects

### Simple Beat-Reactive Effect

```python
class PulsingCircle(Effect):
    name = "Pulsing Circle"
    effect_class = "effect_class43"

    def __init__(self, size: QSize):
        super().__init__(size)
        self.radius = 50.0

    def on_beat(self):
        super().on_beat()
        self.radius = 200.0  # Expand on beat

    def update(self, dt_ms, energies, sensitivity, flash_thresh):
        # Decay back to normal
        self.radius = max(50.0, self.radius - (dt_ms * 0.2))

    def paint(self, p: QPainter, brightness: float):
        p.save()
        w, h = self.size.width(), self.size.height()
        color = QColor(self.color)
        color.setAlphaF(brightness)
        p.setPen(QPen(color, 3))
        p.drawEllipse(QPointF(w/2, h/2), self.radius, self.radius)
        p.restore()
```

### Frequency-Reactive Effect

```python
class FrequencyBars(Effect):
    name = "Frequency Bars"
    effect_class = "effect_class44"

    def update(self, dt_ms, energies, sensitivity, flash_thresh):
        # Store energies for painting
        self.bass = energies.get('low', 0.0) * sensitivity
        self.mid = energies.get('mid', 0.0) * sensitivity
        self.high = energies.get('high', 0.0) * sensitivity

    def paint(self, p: QPainter, brightness: float):
        p.save()
        w, h = self.size.width(), self.size.height()

        # Draw three bars
        bar_width = w / 3
        p.fillRect(0, h - h*self.bass, bar_width, h*self.bass, QColor(255, 0, 0))
        p.fillRect(bar_width, h - h*self.mid, bar_width, h*self.mid, QColor(0, 255, 0))
        p.fillRect(2*bar_width, h - h*self.high, bar_width, h*self.high, QColor(0, 0, 255))

        p.restore()
```

## 🔧 Advanced Features

### Custom Effect Settings

If your effect needs special settings (like the Starfield spacing), add a custom method:

```python
class MyEffect(Effect):
    name = "My Effect"
    effect_class = "effect_class45"

    def __init__(self, size: QSize):
        super().__init__(size)
        self.custom_param = 50

    def set_custom_param(self, value: int):
        self.custom_param = value
```

Then in `src/openlightshow/main.py`, add handling in `set_controls()` (this is the only place you'd need to modify the main script):

```python
def set_controls(self, ...):
    # ...
    for e in self.effects_all:
        if e.name == "My Effect" and hasattr(e, 'set_custom_param'):
            e.set_custom_param(value)
```

### Effect Classification System

Effects are automatically prevented from playing together based on conflict rules defined in `exclude_list.toml`. The system ensures visual diversity by preventing similar effects from running simultaneously.

**How it works:**
- Each effect has an `effect_class` attribute (e.g., `"centereffect_class01"`, `"scanner_class02"`, etc.)
- The `exclude_list.toml` file defines which effect classes cannot play together
- When selecting active effects, the system automatically excludes conflicting effects
- If a conflict occurs, the system randomly replaces one of the conflicting effects with a non-conflicting effect
- This happens automatically based on the configuration!

**Assigning effect classes:**

When creating a new effect, assign it an appropriate `effect_class`:

```python
class MyNewEffect(Effect):
    name = "My New Effect"
    effect_class = "unique_class01"  # Use a unique class, or group with similar effects
```

**Guidelines:**
- Use the same `effect_class` for effects that should never play together (similar visual patterns)
- Use different `effect_class` values for effects that complement each other
- Check `exclude_list.toml` to see existing conflict rules
- Add your effect class to the exclusion rules if needed
- Currently, the system manages 50+ effects with various classes

**Example:**
```python
# These effects should not play together (same scanning pattern)
class RadarSweep(Effect):
    name = "Radar Sweep"
    effect_class = "effect_class29"  # Scanner effects

class ScannerWindmill(Effect):
    name = "Scanner Windmill"
    effect_class = "effect_class33"  # Different scanner pattern

# These can play together (different visual patterns)
class WavingLine(Effect):
    name = "Waving Line"
    effect_class = "effect_class2"  # Line effects

class PixelExplosion(Effect):
    name = "Pixel Explosion"
    effect_class = "effect_class25"  # Particle effects
```

## 🧪 Testing Your Effect

1. **Visual Test**: Run the app and enable only your effect to see it in isolation
2. **Auto-discovery Test**: Verify the effect appears in the effects list when you restart the application
3. **Integration Test**: Enable it with other effects to check compatibility
4. **Audio Reactivity Test**: Play music and verify the effect responds to bass, mids, highs, and beats

## 🎓 Best Practices

1. **Always call `p.save()` and `p.restore()`** in `paint()` to avoid affecting other effects
2. **Keep background black** - don't fill the entire screen unless that's the effect
3. **Use normalized coordinates** when possible (0.0-1.0) and multiply by size
4. **Respect brightness** - multiply alpha/colors by the brightness parameter
5. **Handle resize gracefully** - don't assume fixed dimensions
6. **Use beat debouncing** if your effect creates objects on beats (see BulletHoles)
7. **Test with different sensitivity values** - effects should work from 0.1 to 2.0+

## 📊 Performance Tips

- Limit the number of objects (e.g., max 100 particles)
- Use `QPen.setCosmetic(True)` for lines that shouldn't scale
- Avoid expensive operations in `paint()` - do calculations in `update()`
- Use integer coordinates for `drawLine()`, `drawPoint()`, etc.
- Consider using `QPolygonF` for multiple connected lines

## 🚀 That's It!

The beauty of this architecture is its simplicity:

1. ✅ **No registration needed** - Just drop the file in `src/openlightshow/effects/`
2. ✅ **No imports in main script** - Auto-discovery handles everything
3. ✅ **Self-contained** - Each effect is independent
4. ✅ **Safe to experiment** - Can't break other effects
5. ✅ **Package ready** - Your effect will be included when building the package

## 📦 Installing Your Modified Package

If you've created custom effects and want to install the package:

```bash
# Development install (editable mode)
pip install -e .

# Or build and install the package
pip install build
python -m build
pip install dist/openlightshow-*.whl
```

Happy effect creation! 🎉
