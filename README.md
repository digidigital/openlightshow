# OpenLightShow

A music-reactive lightshow application with 50+ visual effects built with PySide6. Transform your music into stunning visualizations with real-time audio analysis and beat detection.

1. Add a MP3 to your playlist
2. Generate (a lot of) stage smoke
3. Point your beamer / projector in the direction of your audience
4. Start the anmimation
5. Enjoy! 🙋‍♀️🙌🙋🙌🙋‍♂️

Effect preview on [YouTube](https://youtu.be/jf2aq04m4Lg?si=u18eDf1OWQ_chyb_)

![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## Features

- **50+ Visual Effects**: Wide variety of music-reactive effects including:
  - Scanners & Lasers (horizontal/vertical scans, rotating dots, laser planets)
  - Tunnels (circle, hex, rectangular, star tunnels)
  - Particles (fireflies, pixel rain, plasma field, wild shot)
  - Geometric Patterns (kaleidoscope, frequency mandala, breathing grid)
  - Dynamic Effects (electric arc, orbiting satellites, corner burst)

- **Buffered Audio Analysis**:
  - Beat detection and tracking
  - Frequency band separation (bass, mids, highs)
  - Onset strength analysis
  - Energy-based effect modulation

- **Customizable Controls**:
  - Brightness adjustment
  - Sensitivity control
  - Flash threshold
  - Effect rotation interval
  - Individual effect selection/deselection
  - Weights that influence effect use probability
  - Multi-effect layering (1-5 simultaneous effects)

- **Effect Classification System**: Prevents similar effects from playing together for better visual variety

## Installation

### Quick Install

#### Windows Users
Download the standalone EXE installer from the [GitHub Releases page](https://github.com/digidigital/openlightshow/releases). No Python installation required!

#### Python Users (All Platforms)

```bash
# Install from PyPI
pip install openlightshow

# Run the application
openlightshow
```

### Development Install

For developers who want to modify the source code:

```bash
# Clone the repository
git clone https://github.com/digidigital/openlightshow.git
cd openlightshow

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install in development mode
pip install -e .

# Or install with development dependencies
pip install -e .[dev]

# Alternative: Install from requirements.txt
pip install -r requirements.txt

# For development with all tools
pip install -r requirements-dev.txt
```

### Prerequisites

- **Windows**: Use the EXE installer (no prerequisites needed)
- **Linux/Mac/Python install**: Python 3.10 or higher
- **FFmpeg** (optional): For broader audio format support

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install ffmpeg libsndfile1
```

**macOS:**
```bash
brew install ffmpeg libsndfile
```

**Windows:**
Download FFmpeg from [ffmpeg.org](https://ffmpeg.org/download.html) and add it to your PATH.

> **Note**: Modern versions of librosa use `soundfile` as the primary audio backend, which includes MP3 support via libsndfile 1.1.0+. FFmpeg is only needed for legacy format support or if you experience compatibility issues.

## Usage

### Running the Application

After installation, you can run the application in several ways:

**Using the command-line script:**
```bash
openlightshow
```

**Using Python module syntax:**
```bash
python -m openlightshow
```

**Or if running from source without installation:**
```bash
cd /path/to/openlightshow
python -m openlightshow
```

### Quick Start Guide

1. **Load a Track**: Click "Add MP3" and select an audio file. 
2. **Select Effects**: Choose which effects to enable from the effects list
3. **Adjust Settings**:
   - **Brightness**: Control overall effect intensity (10-200%)
   - **Sensitivity**: How responsive effects are to music (0-100%)
   - **Flash Threshold**: Beat detection sensitivity (0-100%)
   - **Max Active**: Number of simultaneous effects (1-5)
   - **Rotation Interval**: How often effects change (1-30 seconds)
4. **Play**: Click the play button to start the lightshow!

## Effect Categories

Effects are internally organized by categories to prevent visual conflicts. The `exclude_list.toml` configuration defines which effect classes cannot play together, ensuring optimal visual variety:

- **Scanner Effects**: Linear scanning patterns
- **Tunnel Effects**: Depth-based expanding/contracting shapes
- **Particle Effects**: Point-based dynamic systems
- **Flash Effects**: Beat-synchronized flashes
- **Geometric Effects**: Pattern-based visualizations
- **Rotation Effects**: Spinning and orbital animations
- **Center Effects**: Effects centered on screen (gobos, kaleidoscopes)
- **Edge Effects**: Effects along screen edges

## Technical Details

### Audio Analysis

The application uses `librosa` for audio analysis:
- **Sample Rate**: 44.1 kHz
- **FFT Size**: 2048
- **Hop Length**: 512 samples
- **Frequency Bands**:
  - Bass: 20-200 Hz
  - Mids: 200-2000 Hz
  - Highs: 2000-8000 Hz

### Dependencies

- **PySide6** (>= 6.5.0): Qt6 GUI framework
- **numpy** (>= 1.24.0): Numerical computations
- **librosa** (>= 0.10.0): Audio analysis and beat detection
- **soundfile** (>= 0.12.0): Audio file I/O

## Creating Custom Effects

OpenLightShow uses a **fully modular plugin-based architecture**. Effects are auto-discovered from the `effects/` directory - just drop in a new file and it's automatically loaded!

### Quick Effect Creation (3 Steps)

1. **Create a new Python file** in `src/openlightshow/effects/`
2. **Subclass the Effect base class**:

```python
from ..effect_base import Effect
from PySide6.QtGui import QPainter, QColor
from PySide6.QtCore import QSize

class MyCustomEffect(Effect):
    name = "My Custom Effect"
    effect_class = "customeffect_class01"  # Unique classification

    def __init__(self, size: QSize):
        super().__init__(size)
        # Initialize your effect state

    def on_beat(self):
        # React to beat detection
        super().on_beat()

    def update(self, dt_ms, energies, sensitivity, flash_thresh):
        # Update effect state
        # energies = {'low': 0.0-1.0, 'mid': 0.0-1.0, 'high': 0.0-1.0}
        pass

    def paint(self, p: QPainter, brightness: float):
        p.save()
        # Draw your effect using QPainter methods
        p.restore()
```

3. **Restart the app** - Your effect will be automatically discovered and appear in the effects list!

### AI-Assisted Effect Creation

Visit the [project website](https://openlightshow.digidigital.de) for a ready-to-use AI prompt that you can copy and paste into ChatGPT, Claude, or Copilot with your effect idea. The prompt includes the complete Effect base class structure and examples.

See [Implementation_guide.md](Implementation_guide.md) for detailed development guidelines, QPainter methods, and best practices. 

## Troubleshooting

### MP3 Files Not Loading

If you encounter issues loading MP3 files:

1. **Check libsndfile version**: Ensure you have libsndfile >= 1.1.0
   ```bash
   python -c "import soundfile; print(soundfile.__version__)"
   ```

2. **Install FFmpeg**: As a fallback, install FFmpeg (see Prerequisites section)

3. **Try WAV format**: Convert your audio to WAV format as a workaround

### Performance Issues

- Reduce the number of simultaneous effects (Max Active setting)
- Lower the brightness setting
- Close other resource-intensive applications

### Effects Not Responding to Music

- Increase the sensitivity slider
- Adjust the flash threshold
- Check that your audio file is being analyzed (watch the console output during track loading)

## License

MIT License - see LICENSE file for details

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-effect`)
3. Commit your changes (`git commit -m 'Add amazing effect'`)
4. Push to the branch (`git push origin feature/amazing-effect`)
5. Open a Pull Request

## Acknowledgments

- Built with [PySide6](https://www.qt.io/qt-for-python)
- Audio analysis powered by [librosa](https://librosa.org/)
- Inspired by music visualization and VJ software

## Authors

- Björn Seipel - Initial work

## Links

- [Project Website](https://openlightshow.digidigital.de)
- [PyPI Package](https://pypi.org/project/openlightshow/)
- [GitHub Repository](https://github.com/digidigital/openlightshow)
- [Windows Installer](https://github.com/digidigital/openlightshow/releases)
- [Issue Tracker](https://github.com/digidigital/openlightshow/issues)
- [Implementation Guide](Implementation_guide.md)

