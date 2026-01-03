"""
PyInstaller entry point for OpenLightShow.

This script is used as the entry point for PyInstaller builds.
It uses absolute imports to avoid relative import issues.
"""

import sys
from openlightshow.main import main

if __name__ == "__main__":
    main()
