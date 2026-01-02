# OpenLightShow - Quick Start Guide

## Running the Application

### Option 1: Command-Line Script (Recommended)
```bash
openlightshow
```

### Option 2: Python Module
```bash
python -m openlightshow
```

### Option 3: From Source Directory
```bash
cd /path/to/openlightshow
python -m openlightshow
```

## Development Setup

### Install in Development Mode
```bash
# Clone or navigate to project directory
cd /path/to/openlightshow

# Create/activate virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in editable mode
pip install -e .
```

### Making Changes
- Edit code in `src/openlightshow/`
- Changes are immediately available (no reinstall needed)
- Test with `python -m openlightshow`

## Creating New Effects

### Step 1: Create Effect File
Create a new file in `src/openlightshow/effects/your_effect.py`:

```python
from ..effect_base import Effect
from PySide6.QtGui import QPainter, QColor
from PySide6.QtCore import QSize

class YourEffect(Effect):
    name = "Your Effect Name"
    effect_class = "youreffect_class01"  # Unique class

    def __init__(self, size: QSize):
        super().__init__(size)
        # Initialize your effect

    def on_beat(self):
        # React to beat detection
        pass

    def update(self, dt_ms, energies, sensitivity, flash_thresh):
        # Update effect state
        self.bass_energy = energies.get('low', 0.0) * sensitivity
        self.mid_energy = energies.get('mid', 0.0) * sensitivity
        self.high_energy = energies.get('high', 0.0) * sensitivity

    def paint(self, p: QPainter, brightness: float):
        p.save()
        # Draw your effect
        # Always clamp alpha: max(0.0, min(1.0, alpha_value))
        p.restore()
```

### Step 2: Test
```bash
python -m openlightshow
```

Your effect will be automatically discovered and loaded!

## Building Distribution

### Build Package
```bash
# Install build tool (if not already installed)
pip install build

# Clean old builds (optional)
rm -rf dist/ build/ *.egg-info

# Build distributions
python -m build
```

### Output
- `dist/openlightshow-X.Y.Z-py3-none-any.whl` - Wheel package
- `dist/openlightshow-X.Y.Z.tar.gz` - Source distribution

## Publishing to PyPI

### Test PyPI (Recommended First)
```bash
# Install twine
pip install twine

# Upload to Test PyPI
twine upload --repository testpypi dist/*

# Test installation
pip install --index-url https://test.pypi.org/simple/ openlightshow
```

### Production PyPI
```bash
# Upload to PyPI
twine upload dist/*

# Anyone can now install with
pip install openlightshow
```

## Updating Version

1. Edit `pyproject.toml`:
```toml
[project]
version = "0.2.0"  # Increment version
```

2. Rebuild:
```bash
python -m build
```

3. Publish new version:
```bash
twine upload dist/*
```

## Project Structure

```
openlightshow/
├── src/openlightshow/       # Main package
│   ├── __init__.py          # Package init
│   ├── __main__.py          # Module entry point
│   ├── main.py              # Main application
│   ├── effect_base.py       # Base effect class
│   ├── effect_loader.py     # Auto-discovery
│   └── effects/             # 52+ effects
├── pyproject.toml           # Package config
├── README.md                # Documentation
├── LICENSE                  # MIT License
└── dist/                    # Built packages
```

## Effect Count

Current effects: **52**
- 47 original effects
- 5 new classic lighting effects:
  - Moonflower
  - Butterfly
  - DiscoBall
  - DerbyLights
  - MovingHeads

## Troubleshooting

### Package Not Found
```bash
# Reinstall in editable mode
pip install -e .
```

### Old Files Conflict
The old `openlightshow.py` in root directory will conflict with the package. It has been renamed to `openlightshow_old.py`.

### Effects Not Loading
Effects must:
- Be in `src/openlightshow/effects/` directory
- Import from `..effect_base`
- Have a `name` class attribute
- Subclass `Effect`

### Import Errors
Make sure you're importing from the package:
```python
# Correct
from openlightshow.effect_base import Effect

# Also correct (from within package)
from ..effect_base import Effect
```

## Quick Commands Reference

```bash
# Run application
python -m openlightshow

# Development install
pip install -e .

# Build package
python -m build

# Publish to PyPI
twine upload dist/*

# Test imports
python -c "from openlightshow import main; print('OK')"

# Count effects
python -c "from openlightshow.effect_loader import discover_effects; print(len(discover_effects()))"
```

## Need Help?

- See `README.md` for detailed documentation
- See `Implementation_guide.md` for effect development
- See `EFFECT_CLASSES.md` for effect classification
