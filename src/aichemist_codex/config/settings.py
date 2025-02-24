"""Global configuration settings for The Aichemist Codex."""

from pathlib import Path

# Define base directories
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
LOG_DIR = DATA_DIR / "logs"
EXPORT_DIR = DATA_DIR / "exports"
CACHE_DIR = DATA_DIR / "cache"

# File settings
DEFAULT_JSON_INDENT = 4
DEFAULT_IGNORE_PATTERNS = {
    "*.pyc",
    "*.pyo",
    "__pycache__",
    "*.class",
    "*.jar",
    "node_modules",
    ".git",
    ".svn",
    ".hg",
    "venv",
    ".venv",
    "myenv",
    "env",
    "build",
    "dist",
    "target",
    ".vscode",
    ".idea",
    ".DS_Store",
    "Thumbs.db",
}

# Application Settings
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB file limit
MAX_TOKENS = 8000  # Token limit for analysis
