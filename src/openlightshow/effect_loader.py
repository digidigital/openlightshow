"""
Effect loader module - automatically discovers and loads all effects from the effects/ directory.
"""

import os
import sys
import importlib
import inspect
from pathlib import Path
from typing import List, Type, Dict
from .effect_base import Effect


def get_resource_path(relative_path):
    """
    Get absolute path to resource, works for dev and for PyInstaller.

    When running as a PyInstaller bundle, resources are extracted to sys._MEIPASS.
    During development, resources are relative to this file.
    """
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        base_path = Path(sys._MEIPASS) / 'openlightshow'
    else:
        # Running in development
        base_path = Path(__file__).parent

    return base_path / relative_path


def discover_effects() -> Dict[str, Type[Effect]]:
    """
    Automatically discover and load all Effect classes from the effects/ directory.

    Returns:
        Dictionary mapping effect names to their class types
    """
    effects_dir = get_resource_path('effects')
    effect_classes = {}

    # Get all .py files in effects/ directory
    if not effects_dir.exists():
        print(f"Warning: effects directory not found at {effects_dir}")
        return effect_classes

    for file_path in effects_dir.glob('*.py'):
        # Skip __init__.py and effect_base.py
        if file_path.name.startswith('__') or file_path.name == 'effect_base.py':
            continue

        module_name = file_path.stem  # filename without extension

        try:
            # Import the module dynamically
            module = importlib.import_module(f'openlightshow.effects.{module_name}')

            # Find all Effect subclasses in the module
            for name, obj in inspect.getmembers(module, inspect.isclass):
                # Check if it's a subclass of Effect (but not Effect itself)
                if issubclass(obj, Effect) and obj is not Effect and hasattr(obj, 'name'):
                    effect_classes[obj.name] = obj
                    print(f"  Loaded effect: {obj.name} from {module_name}.py")

        except Exception as e:
            print(f"  Warning: Failed to load {module_name}.py: {e}")

    return effect_classes


def get_effect_names() -> List[str]:
    """
    Get a sorted list of all available effect names.

    Returns:
        List of effect names (strings)
    """
    effects = discover_effects()
    return sorted(effects.keys())


if __name__ == '__main__':
    print("Discovering effects...")
    effects = discover_effects()
    print(f"\nFound {len(effects)} effects:")
    for name in sorted(effects.keys()):
        print(f"  - {name}")
