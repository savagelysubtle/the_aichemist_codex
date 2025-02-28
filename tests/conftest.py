import sys
from pathlib import Path

# Get the absolute path to the src directory
SRC_DIR = Path(__file__).resolve().parent.parent / "src"

# Dynamically add each package under src to sys.path
for subdir in SRC_DIR.iterdir():
    if subdir.is_dir():
        sys.path.insert(0, str(subdir))

# Ensure the main src directory is included as well
sys.path.insert(0, str(SRC_DIR))
