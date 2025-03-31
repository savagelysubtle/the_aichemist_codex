"""Global settings and configuration constants."""

import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# Project root detection - more robust approach
def determine_project_root() -> Path:
    """
    Determine the project root directory using multiple methods.

    First checks for environment variable, then tries to detect based on
    repository structure, with a fallback to the parent of the src directory.

    Returns:
        Path: The determined project root directory
    """
    # Method 1: Check environment variable
    if "AICHEMIST_ROOT" in os.environ:
        path = Path(os.environ["AICHEMIST_ROOT"])
        if path.exists():
            return path

    # Method 2: Detect based on repository structure
    # Try to find the project root by looking for key files/directories
    current_path = Path(__file__).resolve().parent.parent.parent.parent

    # Common repository root indicators
    indicators = [
        ".git",
        "pyproject.toml",
        "setup.py",
        "README.md",
        "src/the_aichemist_codex",
    ]

    # Check the current directory and any parent directory
    check_path = current_path
    for _ in range(4):  # Limit search depth
        if any((check_path / indicator).exists() for indicator in indicators):
            return check_path
        check_path = check_path.parent

    # Method 3: Fallback to parent of src directory
    if current_path.name == "src":
        return current_path.parent
    elif "src" in [p.name for p in current_path.parents]:
        # Find the parent that contains 'src'
        for parent in current_path.parents:
            if parent.name == "src":
                return parent.parent

    # Last resort: Use the parent of the current file's directory
    return current_path


# Core paths
PROJECT_ROOT = determine_project_root()
SRC_DIR = PROJECT_ROOT / "src"
CACHE_DIR = PROJECT_ROOT / ".cache"
DATA_DIR = PROJECT_ROOT / "data"

# Feature flags
FEATURES = {
    "enable_enhanced_metadata": True,
    "enable_windows_integration": True,
    "enable_regex_search": True,
    "enable_semantic_search": True,
    "enable_similarity_search": True,
}

# Search settings
REGEX_MAX_RESULTS = 100
REGEX_MAX_COMPLEXITY = 50
REGEX_TIMEOUT_MS = 5000  # 5 seconds
SIMILARITY_MAX_RESULTS = 20

# Cache settings
CACHE_TTL = 3600  # 1 hour
MEMORY_CACHE_SIZE = 1000  # items

# File reading settings
MAX_PREVIEW_LENGTH = 500  # characters
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


def get_settings() -> dict[str, Any]:
    """
    Get all settings as a dictionary.

    Returns:
        Dict containing all settings
    """
    # Get all uppercase variables from this module
    return {
        name: value
        for name, value in globals().items()
        if name.isupper() and not name.startswith("_")
    }
