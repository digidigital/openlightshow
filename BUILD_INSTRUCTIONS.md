# Building OpenLightShow Executables

This document describes how to build standalone executables for OpenLightShow using PyInstaller.

## Prerequisites

1. **Python 3.10+** installed
2. **All dependencies** installed:
   ```bash
   # Install runtime dependencies
   pip install -r requirements.txt

   # Install build dependencies (includes PyInstaller)
   pip install -r requirements-build.txt

   # Or install the package in editable mode
   pip install -e .
   ```

## PyInstaller Safety Checklist

The OpenLightShow codebase is **PyInstaller-safe**:

✅ **No multiprocessing** - Uses single-process architecture with Qt event loop
✅ **No threading** - Uses Qt's QTimer for async operations
✅ **Resource path handling** - Uses `get_resource_path()` helper for frozen executables
✅ **Dynamic imports** - Effect loader uses proper module discovery
✅ **All assets bundled** - TOML configs, icons, and effects included in spec file

### Key PyInstaller Adaptations

1. **Resource Path Helper** (`main.py` and `effect_loader.py`):
   ```python
   def get_resource_path(relative_path):
       if getattr(sys, 'frozen', False):
           base_path = Path(sys._MEIPASS)
       else:
           base_path = Path(__file__).parent
       return base_path / relative_path
   ```

2. **All resource loading uses the helper**:
   - TOML configuration files
   - Icon files
   - Effect modules directory

## Building on Windows

### Quick Build

Run the batch script:
```cmd
build_windows.bat
```

### Manual Build

```cmd
# Clean previous builds
rmdir /s /q build dist

# Build
pyinstaller openlightshow.spec

# Output will be in: dist\OpenLightShow\OpenLightShow.exe
```

### Windows Executable Features

- **No console window** - GUI-only application
- **Application icon** - Uses `appicon.ico`
- **Version info** - Embedded from `version_info.txt`
- **All assets bundled** - Self-contained distribution
- **Size optimized** - Excludes unnecessary modules (matplotlib, PIL, tkinter)

## Building on Linux/Mac

### Quick Build

Run the shell script:
```bash
./build_linux.sh
```

### Manual Build

```bash
# Clean previous builds
rm -rf build dist

# Build
pyinstaller openlightshow.spec

# Output will be in: dist/OpenLightShow/OpenLightShow
```

## Spec File Overview

The `openlightshow.spec` file handles:

1. **Data Files**:
   - `presets.toml` - Effect preset configurations
   - `exclude_list.toml` - Effect conflict rules
   - `icons/` - Application icons (ICO, PNG)
   - `effects/` - All effect module files

2. **Hidden Imports**:
   - All effect modules (dynamically collected)
   - PySide6 submodules
   - Audio processing libraries (librosa, soundfile, scipy)
   - TOML parsers

3. **Excluded Modules** (size optimization):
   - matplotlib
   - PIL
   - tkinter
   - pytest
   - setuptools

4. **Executable Settings**:
   - Name: `OpenLightShow`
   - Console: False (Windows GUI mode)
   - Icon: `appicon.ico`
   - UPX compression: Enabled

## File Structure

After building, the distribution folder contains:

```
dist/OpenLightShow/
├── OpenLightShow.exe           # Main executable (Windows)
├── OpenLightShow               # Main executable (Linux/Mac)
├── _internal/                  # PyInstaller runtime files
│   ├── openlightshow/
│   │   ├── effects/           # All effect modules
│   │   ├── icons/             # Icons
│   │   ├── presets.toml       # Configurations
│   │   └── exclude_list.toml
│   ├── PySide6/               # Qt libraries
│   ├── numpy/                 # Dependencies
│   └── ... (other dependencies)
```

## Distribution

### Windows

**Option 1: ZIP Archive**
```cmd
cd dist
powershell Compress-Archive -Path OpenLightShow -DestinationPath OpenLightShow-Windows-v1.0.0.zip
```

**Option 2: Installer (Recommended)**

Use [NSIS](https://nsis.sourceforge.io/) with [NSI-Designer](https://nsi-designer.digidigital.de) to build a Windows-Installer


### Linux

**Option 1: TAR Archive**
```bash
cd dist
tar -czf OpenLightShow-Linux-v1.0.0.tar.gz OpenLightShow/
```

**Option 2: AppImage**

Use [appimagetool](https://appimage.github.io/appimagetool/):

1. Create AppDir structure
2. Add desktop file and icon
3. Build AppImage:
   ```bash
   appimagetool dist/OpenLightShow OpenLightShow-v1.0.0-x86_64.AppImage
   ```

### macOS

**Create .app Bundle**

1. Build with PyInstaller (creates .app automatically on macOS)
2. Code sign (optional but recommended):
   ```bash
   codesign --force --deep --sign - dist/OpenLightShow.app
   ```
3. Create DMG installer:
   ```bash
   hdiutil create -volname "OpenLightShow" -srcfolder dist/OpenLightShow.app \
     -ov -format UDZO OpenLightShow-v1.0.0.dmg
   ```

## Testing the Build

1. **Run the executable**:
   - Windows: `dist\OpenLightShow\OpenLightShow.exe`
   - Linux/Mac: `./dist/OpenLightShow/OpenLightShow`

2. **Test checklist**:
   - [ ] Application launches without errors
   - [ ] Window icon displays correctly
   - [ ] Effects list populates (50+ effects)
   - [ ] Can load MP3 files
   - [ ] Audio playback works
   - [ ] Effects render correctly
   - [ ] Presets load and apply
   - [ ] Settings persist between runs

3. **Test on a clean system** (no Python installed):
   - Copy dist folder to another machine
   - Verify all dependencies are bundled
   - Test full application functionality

## Troubleshooting

### "Module not found" errors

Add missing module to `hiddenimports` in `openlightshow.spec`:
```python
hiddenimports = [
    # ... existing imports ...
    'missing_module_name',
]
```

### Resources not found

Verify resource is in `datas` list in spec file:
```python
datas = [
    ('path/to/resource', 'destination/path'),
]
```

### Large executable size

- Ensure UPX is enabled: `upx=True`
- Add more modules to `excludes` list
- Use `--strip` flag (Linux/Mac)

### Console window appears (Windows)

Set `console=False` in the EXE() section of spec file.

## Version Updates

When releasing a new version:

1. Update `VERSION` in `src/openlightshow/main.py`
2. Update version in `pyproject.toml`
3. Update `filevers` and `prodvers` in `version_info.txt`
4. Rebuild executable
5. Update distribution filenames

## Security Notes

- The executable is **not code-signed** by default
- Windows SmartScreen may warn users on first run
- Code signing requires a certificate (costs money)
- For open-source projects, this is acceptable
- Users can verify integrity via checksums

## CI/CD Integration

For automated builds, see GitHub Actions workflow example:

```yaml
name: Build Executables
on: [push, release]
jobs:
  build-windows:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install -e .
      - run: pip install pyinstaller
      - run: pyinstaller openlightshow.spec
      - uses: actions/upload-artifact@v3
        with:
          name: OpenLightShow-Windows
          path: dist/OpenLightShow/
```

---

For more information, see the [PyInstaller documentation](https://pyinstaller.org/en/stable/).
