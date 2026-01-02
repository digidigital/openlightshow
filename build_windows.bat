@echo off
REM Build script for OpenLightShow Windows executable
REM Requires PyInstaller to be installed: pip install pyinstaller

echo ============================================
echo Building OpenLightShow Windows Executable
echo ============================================
echo.

REM Check if PyInstaller is installed
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo ERROR: PyInstaller is not installed.
    echo Please install it with: pip install pyinstaller
    pause
    exit /b 1
)

REM Clean previous builds
echo Cleaning previous builds...
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist
echo.

REM Build the executable
echo Building executable with PyInstaller...
pyinstaller openlightshow.spec

if errorlevel 1 (
    echo.
    echo ERROR: Build failed!
    pause
    exit /b 1
)

echo.
echo ============================================
echo Build completed successfully!
echo ============================================
echo.
echo Executable location: dist\OpenLightShow\OpenLightShow.exe
echo.
echo You can now:
echo 1. Test the executable: dist\OpenLightShow\OpenLightShow.exe
echo 2. Create an installer using NSIS with NSI-Designer
echo 3. Zip the dist\OpenLightShow folder for distribution
echo.
pause
