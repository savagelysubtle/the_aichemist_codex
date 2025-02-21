from pathlib import Path

# Default output directory
BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "data/processed"
LOG_DIR = BASE_DIR / "data/logs"

# File settings
DEFAULT_JSON_INDENT = 4
MARKDOWN_TEMPLATE = "Project Code Summary"
