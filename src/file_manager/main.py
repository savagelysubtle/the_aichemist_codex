import logging
import os
import sys

from common.utils import load_config, setup_logging
from file_manager.file_watcher import monitor_directory

# Configure logging
LOG_DIR = "logs"
setup_logging(LOG_DIR)
logger = logging.getLogger(__name__)

CONFIG_PATH = "config/config.json"


def main():
    """Entry point for the file manager."""
    if not os.path.exists(CONFIG_PATH):
        logger.error(f"Configuration file not found: {CONFIG_PATH}")
        sys.exit(1)

    config = load_config(CONFIG_PATH)
    directories_to_watch = config["directories_to_watch"]
    rules = config["rules"]

    if not directories_to_watch:
        logger.error("No directories specified to watch. Exiting...")
        sys.exit(1)

    logger.info("🚀 Starting AI-Powered File Manager...")
    monitor_directory(directories_to_watch, rules)


if __name__ == "__main__":
    main()
