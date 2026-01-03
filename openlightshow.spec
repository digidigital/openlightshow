# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for OpenLightShow
Builds a Windows executable with all necessary assets bundled.

Usage:
    pyinstaller openlightshow.spec
"""

from PyInstaller.utils.hooks import collect_data_files, collect_submodules
import os
from pathlib import Path

# Get the project root directory
project_root = Path(SPECPATH)
src_dir = project_root / 'src' / 'openlightshow'

# Collect all effect modules dynamically
effect_modules = collect_submodules('openlightshow.effects')

# Define data files to include
datas = [
    # TOML configuration files
    (str(src_dir / 'presets.toml'), 'openlightshow'),
    (str(src_dir / 'exclude_list.toml'), 'openlightshow'),

    # Icon files
    (str(src_dir / 'icons' / 'appicon.ico'), 'openlightshow/icons'),
    (str(src_dir / 'icons' / 'appicon.png'), 'openlightshow/icons'),

    # All effect files (for auto-discovery)
    (str(src_dir / 'effects'), 'openlightshow/effects'),
]

# Hidden imports - modules that PyInstaller might miss
hiddenimports = [
    'openlightshow.main',
    'openlightshow.effect_base',
    'openlightshow.effect_loader',

    # PySide6 modules
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',
    'PySide6.QtMultimedia',

    # Audio processing libraries
    'numpy',
    'librosa',
    'librosa.feature',
    'librosa.beat',
    'librosa.core',
    'librosa.util',
    'soundfile',
    'scipy',
    'scipy.signal',
    'scipy.fft',

    # TOML parser
    'tomli',
    'tomllib',

    # All effect modules
] + effect_modules

# Binaries - exclude unnecessary files
binaries = []

# Analysis
# NOTE: We use openlightshow_launcher.py instead of __main__.py to avoid
# "attempted relative import with no parent package" error.
# The launcher uses absolute imports which work correctly with PyInstaller.
a = Analysis(
    [str(project_root / 'openlightshow_launcher.py')],
    pathex=[str(project_root / 'src')],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude unnecessary modules to reduce size
        'matplotlib',
        'PIL',
        'tkinter',
        'test',
        'pytest',
        'setuptools',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# Remove duplicate files
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# Create the executable
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='OpenLightShow',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Set to False for GUI-only application (no console window)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(src_dir / 'icons' / 'appicon.ico'),  # Application icon
    version='version_info.txt',  # Optional: Add version info file
)

# Collect all files into a folder
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='OpenLightShow',
)
