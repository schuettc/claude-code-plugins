"""Pytest fixtures + sys.path setup for quality-workflow tests."""

import sys
from pathlib import Path

# Add the lib directory to Python path so tests can `from snapshot import ...`
LIB_DIR = Path(__file__).parent.parent / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))
