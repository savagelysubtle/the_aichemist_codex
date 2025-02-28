"""Script to verify that all imports resolve correctly within the project."""

import importlib.util
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Define the base directory to scan
BASE_DIR = Path(__file__).resolve().parent

# List of Python files to check
python_files = list(BASE_DIR.rglob("*.py"))


# Function to check if a module can be imported
def check_imports(file_path: Path):
    """Checks all imports in a given Python file to ensure they resolve correctly."""
    logger.info(f"Checking imports in {file_path}")

    with file_path.open("r", encoding="utf-8") as f:
        lines = f.readlines()

    for line in lines:
        if line.startswith("import ") or line.startswith("from "):
            try:
                module_name = line.split()[1].split(".")[0]
                if importlib.util.find_spec(module_name) is None:
                    logger.error(
                        f"⚠️  Import issue in {file_path}: '{module_name}' not found"
                    )
            except Exception as e:
                logger.error(f"⚠️  Error parsing import in {file_path}: {e}")


# Run import checks
for file in python_files:
    check_imports(file)
