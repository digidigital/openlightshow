#!/bin/bash
# Build script for OpenLightShow Linux/Mac executable
# Requires PyInstaller to be installed: pip install pyinstaller

echo "============================================"
echo "Building OpenLightShow Executable"
echo "============================================"
echo ""

# Check if PyInstaller is installed
if ! python3 -c "import PyInstaller" 2>/dev/null; then
    echo "ERROR: PyInstaller is not installed."
    echo "Please install it with: pip install pyinstaller"
    exit 1
fi

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build dist
echo ""

# Build the executable
echo "Building executable with PyInstaller..."
pyinstaller openlightshow.spec

if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: Build failed!"
    exit 1
fi

echo ""
echo "============================================"
echo "Build completed successfully!"
echo "============================================"
echo ""
echo "Executable location: dist/OpenLightShow/OpenLightShow"
echo ""
echo "You can now:"
echo "1. Test the executable: ./dist/OpenLightShow/OpenLightShow"
echo "2. Create an AppImage (Linux)"
echo "3. Create a .app bundle (macOS)"
echo "4. Tar/zip the dist/OpenLightShow folder for distribution"
echo ""
