"""Resource and writable-output locations for source and frozen launches."""
import os
import sys
from pathlib import Path


def resource_root() -> Path:
    return Path(sys._MEIPASS) if getattr(sys, 'frozen', False) else Path(__file__).resolve().parents[2]


def resource_path(relative: str) -> Path:
    return resource_root() / relative


def output_directory() -> Path:
    if not getattr(sys, 'frozen', False):
        return resource_root() / 'output'
    base = Path(os.environ.get('LOCALAPPDATA', str(Path.home() / 'AppData' / 'Local')))
    return base / 'BrailleValidator' / 'output'
