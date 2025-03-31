"""Logging configuration for The Aichemist Codex."""

import logging
import sys

from ..settings import determine_project_root

# Define LOG_DIR based on project root
PROJECT_ROOT = determine_project_root()
LOG_DIR = PROJECT_ROOT / "logs"

# Ensure log directory exists
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIR / "project.log"


def setup_logging() -> None:
    """Configures global logging settings."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


setup_logging()
logger = logging.getLogger(__name__)
logger.info("Logging initialized.")
