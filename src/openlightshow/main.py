import sys
import os
import random
import math
import time
import tomllib
import urllib.request
import json
import pickle
import hashlib
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional, Dict, Tuple

import numpy as np
import librosa

from PySide6.QtCore import Qt, QUrl, QTimer, QRectF, QPointF, QSize, QSettings, QThread, Signal
from PySide6.QtGui import QPainter, QColor, QPen, QPolygonF, QBrush, QIcon
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QPushButton, QSlider, QListWidget,
    QFileDialog, QHBoxLayout, QScrollArea, QVBoxLayout, QLabel, QComboBox, QListWidgetItem,
    QLineEdit, QSpinBox, QGridLayout, QCheckBox
)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput

# ---------- Version ----------

VERSION = "v1.0.1"
GITHUB_REPO = "digidigital/openlightshow"  


# ---------- PyInstaller Resource Path Helper ----------

def get_resource_path(relative_path):
    """
    Get absolute path to resource, works for dev and for PyInstaller.

    When running as a PyInstaller bundle, resources are extracted to sys._MEIPASS.
    During development, resources are relative to this file.
    """
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        base_path = Path(sys._MEIPASS)
    else:
        # Running in development
        base_path = Path(__file__).parent

    return base_path / relative_path


# ---------- GitHub Version Checker ----------

class VersionChecker(QThread):
    """Background thread to check for new versions on GitHub."""
    version_checked = Signal(str)  # Emits the latest version string

    def run(self):
        try:
            url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
            req = urllib.request.Request(url, headers={'User-Agent': 'OpenLightShow'})

            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                latest_version = data.get('tag_name', '')
                if latest_version and latest_version != VERSION:
                    self.version_checked.emit(latest_version)
        except Exception:
            # Silently fail - don't display anything if we can't connect
            pass


# ---------- Audio Cache Manager ----------

class AudioCacheManager:
    """Manages cached audio analysis data to speed up loading."""

    def __init__(self):
        # Cache directory in user's home folder
        cache_dir = Path.home() / '.openlightshow' / 'cache'
        cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir = cache_dir

    def _get_cache_key(self, file_path: str) -> Optional[str]:
        """Generate cache key from file path and modification time."""
        path_obj = Path(file_path)
        if not path_obj.exists():
            return None

        # Include file size and mtime for invalidation
        stat = path_obj.stat()
        cache_input = f"{path_obj.absolute()}_{stat.st_size}_{stat.st_mtime}"
        return hashlib.md5(cache_input.encode()).hexdigest()

    def get_cached(self, file_path: str):
        """Retrieve cached analysis if available and valid."""
        cache_key = self._get_cache_key(file_path)
        if not cache_key:
            return None

        cache_file = self.cache_dir / f"{cache_key}.pkl"
        if not cache_file.exists():
            return None

        try:
            with open(cache_file, 'rb') as f:
                analysis = pickle.load(f)
            # Update path in case file was moved
            analysis.path = file_path
            return analysis
        except Exception as e:
            print(f"Failed to load cache for {file_path}: {e}")
            return None

    def save_cached(self, analysis):
        """Save analysis to cache."""
        cache_key = self._get_cache_key(analysis.path)
        if not cache_key:
            return

        cache_file = self.cache_dir / f"{cache_key}.pkl"
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(analysis, f, protocol=pickle.HIGHEST_PROTOCOL)
        except Exception as e:
            print(f"Failed to save cache for {analysis.path}: {e}")

    def clear_cache(self):
        """Delete all cached analysis files."""
        for cache_file in self.cache_dir.glob("*.pkl"):
            try:
                cache_file.unlink()
            except Exception as e:
                print(f"Failed to delete cache file {cache_file}: {e}")


# ---------- Audio Preprocessing Worker Thread ----------

class AudioPreprocessWorker(QThread):
    """Background thread worker for preprocessing audio files and caching results."""

    # Signals
    progress_update = Signal(str, int, int)  # message, current, total
    file_completed = Signal(str, object)  # file_path, TrackAnalysis
    all_complete = Signal()

    def __init__(self, file_paths: List[str], cache_manager: AudioCacheManager, parent=None):
        super().__init__(parent)
        self.file_paths = file_paths
        self.cache_manager = cache_manager
        self._stop_requested = False

    def stop(self):
        """Request the worker to stop processing."""
        self._stop_requested = True

    def run(self):
        """Process all files in the queue."""
        total = len(self.file_paths)

        for idx, file_path in enumerate(self.file_paths):
            if self._stop_requested:
                break

            # Check if already cached
            cached = self.cache_manager.get_cached(file_path)
            if cached:
                self.progress_update.emit(f"Loaded from cache: {Path(file_path).name}", idx + 1, total)
                self.file_completed.emit(file_path, cached)
                continue

            # Analyze the file
            try:
                self.progress_update.emit(f"Analyzing: {Path(file_path).name}", idx + 1, total)
                analysis = analyze_track(file_path)

                # Cache the result
                self.cache_manager.save_cached(analysis)

                self.file_completed.emit(file_path, analysis)
            except Exception as e:
                print(f"Failed to preprocess {file_path}: {e}")
                self.progress_update.emit(f"Failed: {Path(file_path).name}", idx + 1, total)

        if not self._stop_requested:
            self.all_complete.emit()


# ---------- Audio analysis ----------

@dataclass
class TrackAnalysis:
    path: str
    duration_ms: int
    beat_times_ms: List[int]
    band_energy: Dict[str, np.ndarray]
    frame_times_ms: np.ndarray


def analyze_track(path: str, sr: int = 44100) -> TrackAnalysis:
    y, sr = librosa.load(path, sr=sr, mono=True)
    duration_ms = int((len(y) / sr) * 1000)

    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr, onset_envelope=onset_env)
    beat_times = librosa.frames_to_time(beat_frames, sr=sr)
    beat_times_ms = [int(t * 1000) for t in beat_times]

    S = np.abs(librosa.stft(y, n_fft=2048, hop_length=512))
    freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
    times = librosa.frames_to_time(np.arange(S.shape[1]), sr=sr, hop_length=512)
    frame_times_ms = (times * 1000.0).astype(np.int64)

    def band_mask(low_hz: float, high_hz: float):
        return (freqs >= low_hz) & (freqs < high_hz)

    def norm_energy(mask):
        band = S[mask, :]
        energy = band.mean(axis=0)
        return energy / energy.max() if energy.max() > 0 else energy

    band_energy = {
        'low': norm_energy(band_mask(20, 200)),
        'mid': norm_energy(band_mask(200, 2000)),
        'high': norm_energy(band_mask(2000, 8000)),
    }

    return TrackAnalysis(
        path=path,
        duration_ms=duration_ms,
        beat_times_ms=beat_times_ms,
        band_energy=band_energy,
        frame_times_ms=frame_times_ms
    )



# ---------- Effect loading ----------

from .effect_base import Effect
from .effect_loader import discover_effects


# ---------- Preset loading ----------

def load_presets() -> Dict[str, Dict]:
    """Load presets from presets.toml file."""
    presets_file = get_resource_path('presets.toml')
    try:
        with open(presets_file, 'rb') as f:
            presets = tomllib.load(f)
        print(f"Loaded {len(presets)} presets from {presets_file}")
        return presets
    except FileNotFoundError:
        print(f"Warning: Presets file not found at {presets_file}")
        return {}
    except Exception as e:
        print(f"Error loading presets: {e}")
        return {}

# ---------- Audio Analysis Worker Thread ----------

class AudioAnalysisWorker(QThread):
    """Background thread worker for analyzing audio tracks without freezing the UI."""

    # Signals to communicate with the main thread
    progress_update = Signal(str)  # Status message
    partial_analysis = Signal(object)  # Partial TrackAnalysis object (streaming)
    analysis_complete = Signal(object)  # Complete TrackAnalysis object
    analysis_failed = Signal(str)  # Error message

    def __init__(self, file_path: str, cache_manager: AudioCacheManager = None, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.cache_manager = cache_manager

    def run(self):
        """Run the audio analysis in the background thread with streaming updates."""
        try:
            # Stage 1: Load audio file
            self.progress_update.emit(f"Loading audio file...")
            y, sr = librosa.load(self.file_path, sr=44100, mono=True)
            duration_ms = int((len(y) / sr) * 1000)

            # Stage 2: Quick STFT analysis - emit partial result immediately
            self.progress_update.emit(f"Analyzing frequencies...")
            S = np.abs(librosa.stft(y, n_fft=2048, hop_length=512))
            freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
            times = librosa.frames_to_time(np.arange(S.shape[1]), sr=sr, hop_length=512)
            frame_times_ms = (times * 1000.0).astype(np.int64)

            def band_mask(low_hz: float, high_hz: float):
                return (freqs >= low_hz) & (freqs < high_hz)

            def norm_energy(mask):
                band = S[mask, :]
                energy = band.mean(axis=0)
                return energy / energy.max() if energy.max() > 0 else energy

            band_energy = {
                'low': norm_energy(band_mask(20, 200)),
                'mid': norm_energy(band_mask(200, 2000)),
                'high': norm_energy(band_mask(2000, 8000)),
            }

            # Emit partial analysis with frequency data but empty beats
            # This allows the lightshow to start immediately with frequency-reactive effects
            partial = TrackAnalysis(
                path=self.file_path,
                duration_ms=duration_ms,
                beat_times_ms=[],  # No beats yet
                band_energy=band_energy,
                frame_times_ms=frame_times_ms
            )
            self.partial_analysis.emit(partial)
            self.progress_update.emit(f"Effects started, detecting beats...")

            # Stage 3: Beat detection (slower part)
            onset_env = librosa.onset.onset_strength(y=y, sr=sr)
            _, beat_frames = librosa.beat.beat_track(y=y, sr=sr, onset_envelope=onset_env)
            beat_times = librosa.frames_to_time(beat_frames, sr=sr)
            beat_times_ms = [int(t * 1000) for t in beat_times]

            # Emit complete analysis with beats
            complete = TrackAnalysis(
                path=self.file_path,
                duration_ms=duration_ms,
                beat_times_ms=beat_times_ms,
                band_energy=band_energy,
                frame_times_ms=frame_times_ms
            )

            # Cache the complete analysis
            if self.cache_manager:
                self.cache_manager.save_cached(complete)

            self.progress_update.emit(f"Analysis complete!")
            self.analysis_complete.emit(complete)

        except Exception as e:
            error_msg = f"Failed to analyze track: {str(e)}"
            self.analysis_failed.emit(error_msg)


def load_exclude_list() -> Dict[str, list]:
    """Load exclude list from exclude_list.toml file."""
    exclude_file = get_resource_path('exclude_list.toml')
    try:
        with open(exclude_file, 'rb') as f:
            exclude_data = tomllib.load(f)
        print(f"Loaded {len(exclude_data)} exclude groups from {exclude_file}")
        return exclude_data
    except FileNotFoundError:
        print(f"Warning: Exclude list file not found at {exclude_file}")
        return {}
    except Exception as e:
        print(f"Error loading exclude list: {e}")
        return {}

# ---------- Lightshow widget ----------

class LightshowWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setAttribute(Qt.WA_OpaquePaintEvent)
        self.setAutoFillBackground(False)
        self.setStyleSheet("background-color: black;")
        self.setWindowTitle("Lightshow")

        self.effects_all: List[Effect] = []
        self.effects_selected_names: List[str] = []
        self.effects_active: List[Effect] = []
        self.weights: Dict[str, int] = {}
        self.max_active: int = 3

        self.sensitivity = 0.7
        self.brightness = 1.0
        self.flash_thresh = 0.85
        self.starfield_spacing = 50

        self.analysis: Optional[TrackAnalysis] = None
        self.player: Optional[QMediaPlayer] = None
        self.is_playing: bool = False

        self.preview_widgets: List[QWidget] = []  # Store preview widgets to update

        # Load exclude list - groups of effects that cannot play together
        self.exclude_groups: List[List[str]] = []
        exclude_data = load_exclude_list()
        for group_name, effects_list in exclude_data.items():
            if isinstance(effects_list, list):
                self.exclude_groups.append(effects_list)
                print(f"Loaded exclude group '{group_name}': {effects_list}")

        self.timer = QTimer(self)
        self.timer.setInterval(16)
        self.timer.timeout.connect(self.tick)

    def attach_preview(self, preview_widget: QWidget):
        """Attach a preview widget that will be updated when this lightshow updates."""
        self.preview_widgets.append(preview_widget)

    def attach_player(self, player: QMediaPlayer):
        self.player = player

    def set_controls(self, sensitivity: float, brightness: float, flash_thresh: float, starfield_spacing: int):
        self.sensitivity = sensitivity
        self.brightness = brightness
        self.flash_thresh = flash_thresh
        if self.starfield_spacing != starfield_spacing:
            self.starfield_spacing = starfield_spacing
            for e in self.effects_all:
                if e.name == "Starfield" and hasattr(e, 'set_spacing'):
                    e.set_spacing(starfield_spacing)

    def set_max_active(self, k: int):
        self.max_active = max(1, k)

    def set_analysis(self, analysis: Optional[TrackAnalysis]):
        self.analysis = analysis

    def start(self):
        self.timer.start()

    def stop(self):
        self.timer.stop()

    def sizeHint(self):
        return QSize(1280, 720)

    def resizeEvent(self, event):
        for e in self.effects_all:
            e.resize(self.size())

    def set_effects_catalog(self, names: List[str]):
        """Load effects by name using auto-discovery."""
        # Discover all available effects
        effect_classes = discover_effects()

        self.effects_all = []
        self.weights = {}

        for name in names:
            if name in effect_classes:
                # Instantiate the effect
                effect_class = effect_classes[name]
                effect_instance = effect_class(self.size())
                self.effects_all.append(effect_instance)
            else:
                print(f"Warning: Effect '{name}' not found")

        for e in self.effects_all:
            self.weights[e.name] = 10

    def set_active_effects_by_names(self, names: List[str]):
        self.effects_selected_names = names
        self._apply_random_subset()

    def _apply_random_subset(self):
        """
        Select a random subset of effects, ensuring that effects with the same
        effect_class are not played together, and that effects in the same
        exclude group are not played together.
        """
        catalog: Dict[str, Effect] = {e.name: e for e in self.effects_all}
        pool = [catalog[n] for n in self.effects_selected_names if n in catalog]
        if not pool:
            self.effects_active = []
            return

        chosen: List[Effect] = []
        chosen_classes: List[str] = []
        chosen_names: List[str] = []
        k = min(self.max_active, len(pool))

        def is_excluded(effect_name: str) -> bool:
            """Check if effect is excluded due to already chosen effects."""
            for exclude_group in self.exclude_groups:
                # If effect is in this group
                if effect_name in exclude_group:
                    # Check if any chosen effect is also in this group
                    for chosen_name in chosen_names:
                        if chosen_name in exclude_group:
                            return True
            return False

        for _ in range(k):
            # Filter pool to exclude effects with classes already chosen
            # AND effects that are in exclude groups with already chosen effects
            valid_pool = [
                e for e in pool
                if e.effect_class not in chosen_classes
                and not is_excluded(e.name)
            ]

            # If no valid effects remain (all have conflicting classes or exclude groups),
            # try replacing a random chosen effect with a different class effect
            if not valid_pool and pool:
                # Get effects with different classes and not excluded
                different_class_pool = [
                    e for e in pool
                    if e.effect_class not in chosen_classes
                    and not is_excluded(e.name)
                ]

                if not different_class_pool:
                    # All remaining effects conflict, allow any effect to avoid getting stuck
                    if pool:
                        if chosen:
                            # Have chosen effects - replace one to maintain variety
                            candidate = random.choice(pool)

                            # Randomly select a chosen effect to replace
                            replace_idx = random.randint(0, len(chosen) - 1)
                            replaced_effect = chosen[replace_idx]

                            # Replace it
                            chosen[replace_idx] = candidate
                            chosen_classes[replace_idx] = candidate.effect_class
                            chosen_names[replace_idx] = candidate.name

                            # Put replaced effect back in pool, remove new one
                            pool = [p for p in pool if p.name != candidate.name]
                            pool.append(replaced_effect)

                            # Continue to next iteration
                            continue
                        else:
                            # No chosen effects yet - just pick one from pool
                            valid_pool = pool
                    else:
                        # No pool left, stop
                        break
                else:
                    valid_pool = different_class_pool

            if not valid_pool:
                break

            # Weighted random selection from valid pool
            total = sum(max(0, self.weights.get(e.name, 1)) for e in valid_pool)
            if total <= 0:
                break

            r = random.uniform(0, total)
            acc = 0.0
            for e in valid_pool:
                acc += max(0, self.weights.get(e.name, 1))
                if r <= acc:
                    chosen.append(e)
                    chosen_classes.append(e.effect_class)
                    chosen_names.append(e.name)
                    # Remove from pool
                    pool = [p for p in pool if p.name != e.name]
                    break

        self.effects_active = chosen

    def randomize_active_subset(self):
        self._apply_random_subset()

    def tick(self):
        if self.player is None:
            self.is_playing = False
        else:
            self.is_playing = (self.player.playbackState() == QMediaPlayer.PlayingState)

        if not self.is_playing or not self.analysis:
            self.update()
            return

        energies = {'low': 0.0, 'mid': 0.0, 'high': 0.0}
        onbeat = False
        pos = self.player.position()

        bt = self.analysis.beat_times_ms
        if bt:
            idx = np.searchsorted(bt, pos)
            candidates = []
            if idx < len(bt):
                candidates.append(bt[idx])
            if idx > 0:
                candidates.append(bt[idx - 1])
            onbeat = any(abs(pos - b) < 80 for b in candidates)

        ft = self.analysis.frame_times_ms
        if len(ft) > 0:
            fi = np.searchsorted(ft, pos)
            fi = int(np.clip(fi, 0, len(ft) - 1))
            energies = {
                'low': float(self.analysis.band_energy['low'][fi]),
                'mid': float(self.analysis.band_energy['mid'][fi]),
                'high': float(self.analysis.band_energy['high'][fi]),
            }

        dt_ms = self.timer.interval()
        for e in self.effects_active:
            if onbeat:
                e.on_beat()
            e.update(dt_ms, energies, self.sensitivity, self.flash_thresh)

        self.update()
        # Also update any attached preview widgets
        for preview in self.preview_widgets:
            preview.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        p.fillRect(self.rect(), Qt.black)
        if self.is_playing:
            for e in self.effects_active:
                e.paint(p, self.brightness)
        p.end()

    def render_to_painter(self, painter: QPainter, target_rect: QRectF):
        """Render the lightshow to a given painter and rectangle (for preview)."""
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.fillRect(target_rect, Qt.black)

        # Scale and translate to fit target rectangle
        scale_x = target_rect.width() / self.width() if self.width() > 0 else 1.0
        scale_y = target_rect.height() / self.height() if self.height() > 0 else 1.0

        painter.translate(target_rect.x(), target_rect.y())
        painter.scale(scale_x, scale_y)

        if self.is_playing:
            for e in self.effects_active:
                e.paint(painter, self.brightness)

        painter.restore()


# ---------- Preview widget ----------

class PreviewWidget(QWidget):
    """Small preview widget that mirrors the lightshow output."""
    def __init__(self, lightshow: LightshowWidget):
        super().__init__()
        self.lightshow = lightshow
        self.setMinimumSize(320, 180)
        self.setMaximumSize(400, 225)
        self.setStyleSheet("background-color: black; border: 2px solid #444;")

    def paintEvent(self, event):
        p = QPainter(self)
        self.lightshow.render_to_painter(p, QRectF(self.rect()))
        p.end()


# ---------- Main application ----------

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"OpenLightShow Controller {VERSION}")

        # Set window icon
        icon_path = get_resource_path('icons/appicon.png')
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        # Initialize QSettings for persistent configuration
        self.settings = QSettings("OpenLightShow", "LightshowController")

        # Flag to prevent saving during initialization
        self._loading_settings = False

        # Start version checker in background
        self.version_checker = VersionChecker()
        self.version_checker.version_checked.connect(self.on_new_version_available)
        self.version_checker.start()

        self.player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.player.setAudioOutput(self.audio_output)

        # Load presets from TOML file
        self.presets = load_presets()

        # Audio cache manager
        self.cache_manager = AudioCacheManager()

        # Audio analysis worker thread
        self.analysis_worker = None

        # Audio preprocessing worker thread
        self.preprocess_worker = None
        self.preprocessed_cache = {}  # file_path -> TrackAnalysis

        # Create status bar
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")

        central = QWidget(self)
        self.setCentralWidget(central)
        root = QHBoxLayout(central)

        # Left: playlist and transport
        left = QVBoxLayout()
        root.addLayout(left, 1)

        left.addWidget(QLabel("Playlist"))
        self.playlist = QListWidget()
        left.addWidget(self.playlist)

        btns = QHBoxLayout()
        self.btn_add = QPushButton("Add MP3")
        self.btn_remove = QPushButton("Remove")
        btns.addWidget(self.btn_add)
        btns.addWidget(self.btn_remove)
        left.addLayout(btns)

        transport = QHBoxLayout()
        self.btn_play = QPushButton("Play")
        self.btn_play.setFocusPolicy(Qt.NoFocus)  # Prevent Space from triggering buttons directly
        self.btn_pause = QPushButton("Pause / Resume")
        self.btn_pause.setFocusPolicy(Qt.NoFocus)
        self.btn_stop = QPushButton("Stop")
        self.btn_stop.setFocusPolicy(Qt.NoFocus)
        transport.addWidget(self.btn_play)
        transport.addWidget(self.btn_pause)
        transport.addWidget(self.btn_stop)
        left.addLayout(transport)

        # Controls
        def mk_slider(label, minv, maxv, init, step=1):
            box = QVBoxLayout()
            lab = QLabel(label)
            sld = QSlider(Qt.Horizontal)
            sld.setRange(minv, maxv)
            sld.setValue(init)
            sld.setSingleStep(step)
            box.addWidget(lab)
            box.addWidget(sld)
            return box, sld

        box_sens, self.sld_sens = mk_slider("Sensitivity", 0, 100, 70)
        box_bright, self.sld_brightness = mk_slider("Brightness", 10, 200, 100)
        box_flash, self.sld_flash_thresh = mk_slider("Flash threshold", 50, 100, 85)
        left.addLayout(box_sens)
        left.addLayout(box_bright)
        left.addLayout(box_flash)

        # Effect change interval (float input)
        box_period = QVBoxLayout()
        lab_period = QLabel("Change effects every (s, float)")
        self.txt_effect_period = QLineEdit("8.0")
        box_period.addWidget(lab_period)
        box_period.addWidget(self.txt_effect_period)
        left.addLayout(box_period)

        # Max active effects (min 1)
        box_max = QVBoxLayout()
        lab_max = QLabel("Max simultaneously active effects (min 1)")
        self.spin_max_active = QSpinBox()
        self.spin_max_active.setRange(1, 10)
        self.spin_max_active.setValue(3)
        box_max.addWidget(lab_max)
        box_max.addWidget(self.spin_max_active)
        left.addLayout(box_max)

        # Starfield spacing slider
        box_star, self.sld_star_spacing = mk_slider("Starfield spacing (px)", 20, 200, 50)
        left.addLayout(box_star)

        presets_box = QHBoxLayout()
        presets_box.addWidget(QLabel("Preset"))
        self.cmb_presets = QComboBox()
        # Add placeholder as first item
        self.cmb_presets.addItem("-- Select Preset --")
        # Populate presets from loaded TOML file
        if self.presets:
            self.cmb_presets.addItems(sorted(self.presets.keys()))
        else:
            # Fallback if presets file not loaded
            self.cmb_presets.addItems(["Default", "Energetic", "Chill, Classic Scan", "Laser Show", "Rave"])
        presets_box.addWidget(self.cmb_presets)
        left.addLayout(presets_box)

        # Right: effects selection and weights combined
        right = QVBoxLayout()
        root.addLayout(right, 2)

        # Preview widget at the top
        right.addWidget(QLabel("Lightshow Preview"))
        # Preview will be created after lightshow widget is initialized
        self.preview_placeholder = QLabel("Preview loading...")
        self.preview_placeholder.setMinimumSize(320, 180)
        self.preview_placeholder.setMaximumSize(400, 225)
        self.preview_placeholder.setStyleSheet("background-color: black; border: 2px solid #444;")
        self.preview_placeholder.setAlignment(Qt.AlignCenter)
        right.addWidget(self.preview_placeholder)

        right.addWidget(QLabel("Effects (✓ to enable, set weight to higher value for higher selection probability, effects of the same category do not play at the same time"))

        # Combined effects list with checkboxes and inline weight spinboxes
        self.effects_panel = QWidget()
        effects_grid = QGridLayout(self.effects_panel)
        effects_grid.setContentsMargins(0, 0, 0, 0)
        effects_grid.setSpacing(4)

        # Set column stretch: checkbox narrow, weight narrow, name wide
        effects_grid.setColumnStretch(0, 0)  # Checkbox column - no stretch, minimal size
        effects_grid.setColumnStretch(1, 0)  # Weight column - no stretch, minimal size
        effects_grid.setColumnStretch(2, 1)  # Effect name - takes remaining space

        # Header row: Enable, Weight, Effect Name
        effects_grid.addWidget(QLabel("<b>Enable</b>"), 0, 0, Qt.AlignCenter)
        effects_grid.addWidget(QLabel("<b>Weight</b>"), 0, 1)
        effects_grid.addWidget(QLabel("<b>Effect Name</b>"), 0, 2)

        self.effect_names = sorted(discover_effects().keys())
        self.effect_checkboxes: Dict[str, QCheckBox] = {}
        self.weight_spinboxes: Dict[str, QSpinBox] = {}

        default_checked = []

        for i, nm in enumerate(self.effect_names):
            row = i + 1  # +1 for header row

            # Checkbox (column 0)
            checkbox = QCheckBox()
            checkbox.setChecked(nm in default_checked)
            checkbox.setMaximumWidth(30)  # Make checkbox column very narrow
            self.effect_checkboxes[nm] = checkbox
            effects_grid.addWidget(checkbox, row, 0, Qt.AlignCenter)

            # Weight spinbox (column 1)
            spin = QSpinBox()
            spin.setRange(0, 100)
            spin.setValue(10)
            spin.setMaximumWidth(60)  # Reduced width to fit content tightly
            spin.setMinimumWidth(60)
            self.weight_spinboxes[nm] = spin
            effects_grid.addWidget(spin, row, 1, Qt.AlignLeft)

            # Effect name label (column 2)
            name_label = QLabel(nm)
            effects_grid.addWidget(name_label, row, 2)

        # Wrap in scroll area
        effects_scroll = QScrollArea()
        effects_scroll.setWidgetResizable(True)
        effects_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        effects_scroll.setWidget(self.effects_panel)
        right.addWidget(effects_scroll)


        # Lightshow output window
        self.lightshow = LightshowWidget()
        self.lightshow.attach_player(self.player)
        self.lightshow.set_effects_catalog(self.effect_names)
        self.apply_effects_selection()
        self.sync_weights_to_widget()
        self.lightshow.set_max_active(self.spin_max_active.value())

        # Replace preview placeholder with actual preview widget
        right.removeWidget(self.preview_placeholder)
        self.preview_placeholder.deleteLater()
        self.preview = PreviewWidget(self.lightshow)
        right.insertWidget(1, self.preview)  # Insert after the "Lightshow Preview" label
        self.lightshow.attach_preview(self.preview)  # Connect preview to lightshow updates

        # Effect rotation timer
        self.effect_rotation_timer = QTimer(self)
        self.effect_rotation_timer.timeout.connect(self.randomize_effects)

        # Connections
        self.btn_add.clicked.connect(self.add_mp3)
        self.btn_remove.clicked.connect(self.remove_selected)
        self.btn_play.clicked.connect(self.play_selected)
        self.btn_pause.clicked.connect(self.pause_playback)
        self.btn_stop.clicked.connect(self.stop_playback)

        self.player.mediaStatusChanged.connect(self.on_media_status)
        self.player.playbackStateChanged.connect(self.on_playback_state)

        self.sld_sens.valueChanged.connect(self.update_controls)
        self.sld_brightness.valueChanged.connect(self.update_controls)
        self.sld_flash_thresh.valueChanged.connect(self.update_controls)
        self.sld_star_spacing.valueChanged.connect(self.update_controls)
        self.txt_effect_period.editingFinished.connect(self.update_rotation_interval)
        self.spin_max_active.valueChanged.connect(self.on_max_active_changed)
        # Connect all effect checkboxes to apply selection and save
        for nm, checkbox in self.effect_checkboxes.items():
            checkbox.stateChanged.connect(lambda _: (self.apply_effects_selection(), self.save_settings()))
        for nm, spin in self.weight_spinboxes.items():
            spin.valueChanged.connect(self.sync_weights_to_widget)
            spin.valueChanged.connect(self.save_settings)
        self.cmb_presets.currentTextChanged.connect(self.apply_preset)

        # Connect all UI elements to save settings on change
        self.sld_sens.valueChanged.connect(self.save_settings)
        self.sld_brightness.valueChanged.connect(self.save_settings)
        self.sld_flash_thresh.valueChanged.connect(self.save_settings)
        self.sld_star_spacing.valueChanged.connect(self.save_settings)
        self.txt_effect_period.editingFinished.connect(self.save_settings)
        self.spin_max_active.valueChanged.connect(self.save_settings)
        self.cmb_presets.currentTextChanged.connect(self.save_settings)

        self.setup_screens()
        self.update_controls()
        self.update_rotation_interval()

        # Install event filter to catch Space key globally
        QApplication.instance().installEventFilter(self)

        # Set up timer to monitor screen changes and swap if needed
        self.screen_monitor_timer = QTimer(self)
        self.screen_monitor_timer.timeout.connect(self.check_screen_swap)
        self.screen_monitor_timer.start(2000)  # Check every 2 seconds

        # Track last swap to prevent rapid repeated swaps
        self._last_swap_time = 0

        # Load saved settings after UI is fully initialized
        self.load_settings()

    def eventFilter(self, obj, event):
        """Global event filter to catch Space key presses."""
        if event.type() == event.Type.KeyPress and event.key() == Qt.Key_Space:
            # Only trigger if the focus is not on a text input field
            focused = QApplication.focusWidget()
            if not isinstance(focused, QLineEdit):
                self.pause_playback()
                return True  # Event handled
        return super().eventFilter(obj, event)

    def setup_screens(self):
        """Initial screen setup - place lightshow on second screen if available."""
        screens = QApplication.screens()
        if len(screens) > 1:
            # Place lightshow on screen[1] (second screen)
            second = screens[1]
            screen_geo = second.geometry()

            # Set lightshow to fullscreen on second screen
            self.lightshow.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
            self.lightshow.setGeometry(screen_geo)
            self.lightshow.showFullScreen()
        else:
            self.lightshow.setWindowFlags(Qt.FramelessWindowHint)
            self.lightshow.showFullScreen()

    def check_screen_swap(self):
        """Check if controller and lightshow are on same screen, and swap if needed."""
        try:
            screens = QApplication.screens()
            if len(screens) <= 1:
                return  # Nothing to swap with single screen

            # Get the screen that the controller window is on
            controller_screen = self.screen()
            if controller_screen is None:
                return

            lightshow_screen = self.lightshow.screen()
            if lightshow_screen is None:
                return

            # Check if they're on the same screen
            if controller_screen == lightshow_screen:
                # Prevent rapid repeated swaps (minimum 3 seconds between swaps)
                current_time = time.time()
                if current_time - self._last_swap_time < 3.0:
                    return

                # Find the first available screen that's not the controller screen
                for screen in screens:
                    if screen != controller_screen:
                        # Move lightshow to this screen
                        screen_geo = screen.geometry()

                        # Use normal window first, then switch to fullscreen
                        self.lightshow.setWindowFlags(Qt.Window)
                        self.lightshow.setGeometry(screen_geo)
                        self.lightshow.show()

                        # Small delay before going fullscreen
                        def make_fullscreen():
                            self.lightshow.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
                            self.lightshow.showFullScreen()

                        QTimer.singleShot(100, make_fullscreen)

                        # Update swap time
                        self._last_swap_time = current_time
                        break
        except Exception:
            # Silently handle any errors to prevent crashes
            pass

    def get_default_music_folder(self) -> str:
        """Get the default music folder based on OS, with fallbacks."""
        # Check if we have a saved folder from previous use
        saved_folder = self.settings.value("last_music_folder", "", type=str)
        if saved_folder and os.path.isdir(saved_folder):
            return saved_folder

        # Get user's home directory
        home = Path.home()

        # Try OS-specific music folders
        if sys.platform == "win32":
            # Windows: ~/Music
            music_folder = home / "Music"
        elif sys.platform == "darwin":
            # macOS: ~/Music
            music_folder = home / "Music"
        else:
            # Linux/Unix: Try XDG_MUSIC_DIR first, then ~/Music
            try:
                # Try to get XDG music directory
                xdg_config = home / ".config" / "user-dirs.dirs"
                if xdg_config.exists():
                    with open(xdg_config, 'r') as f:
                        for line in f:
                            if line.startswith('XDG_MUSIC_DIR'):
                                # Parse: XDG_MUSIC_DIR="$HOME/Music"
                                folder = line.split('=')[1].strip().strip('"')
                                folder = folder.replace('$HOME', str(home))
                                music_folder = Path(folder)
                                break
                        else:
                            music_folder = home / "Music"
                else:
                    music_folder = home / "Music"
            except Exception:
                music_folder = home / "Music"

        # Check if music folder exists, otherwise use home
        if music_folder.exists() and music_folder.is_dir():
            return str(music_folder)
        else:
            return str(home)

    def add_mp3(self):
        # Get the starting directory
        start_dir = self.get_default_music_folder()

        path, _ = QFileDialog.getOpenFileName(
            self,
            "Add audio",
            start_dir,
            "Audio Files (*.mp3 *.wav)"
        )
        if path:
            self.playlist.addItem(QListWidgetItem(path))
            # Save the folder for next time
            folder = os.path.dirname(path)
            self.settings.setValue("last_music_folder", folder)
            self.save_settings()

            # Start preprocessing this file in the background
            self.start_preprocessing([path])

    def remove_selected(self):
        for it in self.playlist.selectedItems():
            file_path = it.text()
            self.playlist.takeItem(self.playlist.row(it))

            # Clean up cached data for this file
            self.clean_file_cache(file_path)

        self.save_settings()

    def play_selected(self):
        # If no selection, play first
        item = self.playlist.currentItem()
        if item is None and self.playlist.count() > 0:
            self.playlist.setCurrentRow(0)
            item = self.playlist.currentItem()
        if not item:
            return

        path = item.text()

        # Check if file exists
        if not os.path.isfile(path):
            # Remove missing file from playlist
            current_row = self.playlist.currentRow()
            self.playlist.takeItem(current_row)

            # Try to play next file if available
            if self.playlist.count() > 0:
                # If we removed the last item, play the new last item
                if current_row >= self.playlist.count():
                    self.playlist.setCurrentRow(self.playlist.count() - 1)
                else:
                    # Play the item that's now at the current row
                    self.playlist.setCurrentRow(current_row)
                # Recursively try to play the next file
                self.play_selected()
            return

        # Set source but don't play yet - wait for analysis
        # This prevents audio stutter during initial file load
        self.player.setSource(QUrl.fromLocalFile(path))

        # Check if we have preprocessed/cached data
        cached_analysis = self.preprocessed_cache.get(path) or self.cache_manager.get_cached(path)

        if cached_analysis:
            # Use cached data - instant playback!
            self.status_bar.showMessage(f"Playing (from cache): {os.path.basename(path)}")
            self.player.play()
            self.lightshow.set_analysis(cached_analysis)
            self.lightshow.start()
        else:
            # Start background analysis to avoid UI freeze
            self.status_bar.showMessage(f"Loading audio: {os.path.basename(path)}...")

            # Cancel any existing analysis worker
            if self.analysis_worker and self.analysis_worker.isRunning():
                self.analysis_worker.quit()
                self.analysis_worker.wait()

            # Create and start new analysis worker
            # Music will start in on_partial_analysis() when first data is ready
            self.analysis_worker = AudioAnalysisWorker(path, self.cache_manager, parent=self)
            self.analysis_worker.progress_update.connect(self.on_analysis_progress)
            self.analysis_worker.partial_analysis.connect(self.on_partial_analysis)
            self.analysis_worker.analysis_complete.connect(self.on_analysis_complete)
            self.analysis_worker.analysis_failed.connect(self.on_analysis_failed)
            self.analysis_worker.start()

    def pause_playback(self):
        """Toggle between pause and resume."""
        if self.player.playbackState() == QMediaPlayer.PlayingState:
            self.player.pause()
        elif self.player.playbackState() == QMediaPlayer.PausedState:
            self.player.play()

    def stop_playback(self):
        self.player.stop()

    def on_analysis_progress(self, message: str):
        """Update status bar with analysis progress."""
        self.status_bar.showMessage(message)

    def on_partial_analysis(self, analysis: TrackAnalysis):
        """Handle partial audio analysis - start playback and effects with frequency data."""
        # Now that we have initial analysis data, start playing the music
        self.player.play()

        # Start effects with frequency-reactive behavior
        self.lightshow.set_analysis(analysis)
        self.lightshow.start()

        # Continue showing progress in status bar
        # (analysis_complete will update it when beats are ready)

    def on_analysis_complete(self, analysis: TrackAnalysis):
        """Handle complete audio analysis - update with beat detection."""
        self.lightshow.set_analysis(analysis)
        # Lightshow is already started by partial_analysis, just update the data
        filename = os.path.basename(analysis.path)
        self.status_bar.showMessage(f"Ready - Playing: {filename}", 5000)

    def on_analysis_failed(self, error_message: str):
        """Handle audio analysis failure - still play music without effects."""
        self.status_bar.showMessage(f"Analysis failed: {error_message} - Playing without effects", 10000)
        print(f"Audio analysis error: {error_message}")

        # Still play the music even if analysis failed
        self.player.play()

    def start_preprocessing(self, file_paths: List[str]):
        """Start preprocessing audio files in the background."""
        if not file_paths:
            return

        # Stop existing preprocessing worker if running
        if self.preprocess_worker and self.preprocess_worker.isRunning():
            self.preprocess_worker.stop()
            self.preprocess_worker.wait()

        # Create and start new worker
        self.preprocess_worker = AudioPreprocessWorker(file_paths, self.cache_manager, parent=self)
        self.preprocess_worker.progress_update.connect(self.on_preprocess_progress)
        self.preprocess_worker.file_completed.connect(self.on_preprocess_file_complete)
        self.preprocess_worker.all_complete.connect(self.on_preprocess_all_complete)
        self.preprocess_worker.start()

    def on_preprocess_progress(self, message: str, current: int, total: int):
        """Handle preprocessing progress updates."""
        self.status_bar.showMessage(f"Preprocessing ({current}/{total}): {message}")

    def on_preprocess_file_complete(self, file_path: str, analysis):
        """Handle completion of a single file preprocessing."""
        # Store in memory cache for instant access
        self.preprocessed_cache[file_path] = analysis

    def on_preprocess_all_complete(self):
        """Handle completion of all preprocessing."""
        self.status_bar.showMessage("All files preprocessed and ready", 3000)

    def clean_file_cache(self, file_path: str):
        """Remove cached data for a specific file."""
        # Remove from in-memory cache
        if file_path in self.preprocessed_cache:
            del self.preprocessed_cache[file_path]

        # Remove from disk cache
        cache_key = self.cache_manager._get_cache_key(file_path)
        if cache_key:
            cache_file = self.cache_manager.cache_dir / f"{cache_key}.pkl"
            if cache_file.exists():
                try:
                    cache_file.unlink()
                    print(f"Deleted cache file for: {file_path}")
                except Exception as e:
                    print(f"Failed to delete cache file for {file_path}: {e}")

    def on_playback_state(self, state):
        self.lightshow.is_playing = (state == QMediaPlayer.PlayingState)
        self.lightshow.update()

        # Update pause button text based on state
        if state == QMediaPlayer.PlayingState:
            self.btn_pause.setText("Pause")
            # Start effect rotation timer when music actually starts playing
            self.randomize_effects()
            # Restart the rotation timer
            self.update_rotation_interval()
        elif state == QMediaPlayer.PausedState:
            self.btn_pause.setText("Resume")
        else:  # Stopped
            self.btn_pause.setText("Pause / Resume")
            # Stop effect rotation timer when music stops
            self.effect_rotation_timer.stop()

    def on_media_status(self, status):
        # Auto-advance to next track
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            current_row = self.playlist.currentRow()
            next_row = current_row + 1
            if next_row < self.playlist.count():
                self.playlist.setCurrentRow(next_row)
                self.play_selected()
            else:
                self.lightshow.is_playing = False
                self.player.stop()
                self.lightshow.update()

    def update_controls(self):
        sensitivity = self.sld_sens.value() / 100.0
        brightness = self.sld_brightness.value() / 100.0
        flash_thresh = self.sld_flash_thresh.value() / 100.0
        spacing = int(self.sld_star_spacing.value())
        self.lightshow.set_controls(sensitivity, brightness, flash_thresh, spacing)

    def update_rotation_interval(self):
        text = self.txt_effect_period.text().strip()
        try:
            seconds = float(text)
            if seconds <= 0:
                raise ValueError
        except ValueError:
            seconds = 20.0
            self.txt_effect_period.setText(f"{seconds:.1f}")
        self.effect_rotation_timer.stop()
        self.effect_rotation_timer.start(int(seconds * 1000))

    def on_max_active_changed(self, val: int):
        self.lightshow.set_max_active(val)
        self.randomize_effects()

    def randomize_effects(self):
        self.sync_weights_to_widget()
        self.lightshow.randomize_active_subset()

    def apply_effects_selection(self):
        names = []
        for nm, checkbox in self.effect_checkboxes.items():
            if checkbox.isChecked():
                names.append(nm)
        self.lightshow.set_active_effects_by_names(names)

    def sync_weights_to_widget(self):
        for nm, spin in self.weight_spinboxes.items():
            self.lightshow.weights[nm] = int(spin.value())

    def apply_preset(self, name: str):
        """Apply a preset from the loaded presets configuration."""
        # Ignore placeholder selection
        if not name or name == "-- Select Preset --" or name not in self.presets:
            if name and name != "-- Select Preset --":
                print(f"Warning: Preset '{name}' not found")
            return

        preset = self.presets[name]

        # Apply settings from preset
        self.sld_sens.setValue(preset.get('sensitivity', 70))
        self.sld_brightness.setValue(preset.get('brightness', 100))
        self.sld_flash_thresh.setValue(preset.get('flash_threshold', 85))
        self.txt_effect_period.setText(str(preset.get('effect_period', 20.0)))
        self.sld_star_spacing.setValue(preset.get('star_spacing', 50))
        self.spin_max_active.setValue(preset.get('max_active', 3))

        # Apply effect selection
        selected_effects = preset.get('effects', [])
        for nm, checkbox in self.effect_checkboxes.items():
            if not selected_effects:
                # Empty list means all effects enabled
                checkbox.setChecked(True)
            else:
                # Check if effect is in the preset's effect list
                checkbox.setChecked(nm in selected_effects)

        # Apply effect weights if present in preset
        effect_weights = preset.get('effect_weights', {})
        if effect_weights:
            for nm, spin in self.weight_spinboxes.items():
                if nm in effect_weights:
                    spin.setValue(int(effect_weights[nm]))

        self.apply_effects_selection()
        self.update_rotation_interval()
        self.randomize_effects()

    def save_settings(self):
        """Save all UI settings to QSettings."""
        # Don't save while we're loading settings
        if self._loading_settings:
            return

        # Save slider values
        self.settings.setValue("sensitivity", self.sld_sens.value())
        self.settings.setValue("brightness", self.sld_brightness.value())
        self.settings.setValue("flash_threshold", self.sld_flash_thresh.value())
        self.settings.setValue("star_spacing", self.sld_star_spacing.value())

        # Save text inputs
        self.settings.setValue("effect_period", self.txt_effect_period.text())

        # Save spinbox
        self.settings.setValue("max_active", self.spin_max_active.value())

        # Save preset selection (skip placeholder)
        current_preset = self.cmb_presets.currentText()
        if current_preset != "-- Select Preset --":
            self.settings.setValue("selected_preset", current_preset)

        # Save checked effects
        checked_effects = []
        for nm, checkbox in self.effect_checkboxes.items():
            if checkbox.isChecked():
                checked_effects.append(nm)
        self.settings.setValue("checked_effects", checked_effects)

        # Save effect weights
        weights = {}
        for nm, spin in self.weight_spinboxes.items():
            weights[nm] = spin.value()
        self.settings.setValue("effect_weights", weights)

        # Save playlist
        playlist_items = []
        for i in range(self.playlist.count()):
            playlist_items.append(self.playlist.item(i).text())
        self.settings.setValue("playlist", playlist_items)

    def load_settings(self):
        """Load all UI settings from QSettings."""
        # Set flag to prevent saving while loading
        self._loading_settings = True

        # Load slider values with defaults
        self.sld_sens.setValue(self.settings.value("sensitivity", 70, type=int))
        self.sld_brightness.setValue(self.settings.value("brightness", 100, type=int))
        self.sld_flash_thresh.setValue(self.settings.value("flash_threshold", 85, type=int))
        self.sld_star_spacing.setValue(self.settings.value("star_spacing", 50, type=int))

        # Load text inputs
        self.txt_effect_period.setText(self.settings.value("effect_period", "20.0", type=str))

        # Load spinbox
        self.spin_max_active.setValue(self.settings.value("max_active", 3, type=int))

        # Don't load preset selection - always show "-- Select Preset --" on startup
        # (preset dropdown should remain at index 0)

        # Load checked effects
        checked_effects = self.settings.value("checked_effects", [], type=list)
        if checked_effects:
            for nm, checkbox in self.effect_checkboxes.items():
                checkbox.setChecked(nm in checked_effects)
            self.apply_effects_selection()

        # Load effect weights
        # QSettings doesn't support dict type, so we load it without type conversion
        saved_weights = self.settings.value("effect_weights", {})
        if saved_weights and isinstance(saved_weights, dict):
            for nm, spin in self.weight_spinboxes.items():
                if nm in saved_weights:
                    spin.setValue(int(saved_weights[nm]))

        # Load playlist - only add files that still exist
        saved_playlist = self.settings.value("playlist", [])
        # Handle QSettings quirk: single-item lists may be returned as strings
        valid_files = []
        if saved_playlist:
            if isinstance(saved_playlist, str):
                saved_playlist = [saved_playlist]
            for path in saved_playlist:
                # Only add files that still exist
                if os.path.isfile(path):
                    self.playlist.addItem(QListWidgetItem(path))
                    valid_files.append(path)

        # Clear the loading flag now that we're done
        self._loading_settings = False

        # Start preprocessing all playlist files in the background
        if valid_files:
            self.start_preprocessing(valid_files)

    def on_new_version_available(self, latest_version: str):
        """Called when a new version is available on GitHub."""
        # Update window title to show new version available
        self.setWindowTitle(f"OpenLightShow Controller {VERSION} (New version available: {latest_version})")

    def closeEvent(self, event):
        # Save settings before closing
        self.save_settings()

        # Stop and wait for analysis worker thread
        try:
            if self.analysis_worker and self.analysis_worker.isRunning():
                self.analysis_worker.quit()
                self.analysis_worker.wait(2000)  # Wait up to 2 seconds
        except Exception:
            pass

        # Stop and wait for preprocessing worker thread
        try:
            if self.preprocess_worker and self.preprocess_worker.isRunning():
                self.preprocess_worker.stop()
                self.preprocess_worker.wait(2000)  # Wait up to 2 seconds
        except Exception:
            pass

        try:
            self.effect_rotation_timer.stop()
        except Exception:
            pass
        try:
            self.player.stop()
        except Exception:
            pass
        try:
            self.lightshow.close()
        except Exception:
            pass
        event.accept()


def main():
    app = QApplication(sys.argv)

    # Set application icon globally
    icon_path = get_resource_path('icons/appicon.png')
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    win = MainWindow()

    # Maximize the window properly (respects taskbar on all platforms)
    # Show the window first as a normal window
    win.show()

    # Defer maximization using QTimer to ensure event loop is running
    # This is especially important on Ubuntu/GNOME where the window manager
    # may delay maximization until the window is fully initialized
    def do_maximize():
        win.setWindowState(Qt.WindowMaximized)
        win.showMaximized()
        win.activateWindow()
        win.raise_()

    # Execute maximization after event loop starts (0ms delay)
    QTimer.singleShot(0, do_maximize)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
