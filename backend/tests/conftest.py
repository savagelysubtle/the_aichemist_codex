import logging
import os
import sys
from pathlib import Path

import pytest

# Get the absolute path to the src directory
SRC_DIR = Path(__file__).resolve().parent.parent / "src"

# Dynamically add each package under src to sys.path
for subdir in SRC_DIR.iterdir():
    if subdir.is_dir():
        sys.path.insert(0, str(subdir))

# Ensure the main src directory is included as well
sys.path.insert(0, str(SRC_DIR))


@pytest.fixture(autouse=True)
def new_log_file(tmp_path_factory):
    """
    Resets the root logger's FileHandler before each test so that a new log file is used.
    This prevents log messages from accumulating across tests.
    """
    # Create a new temporary directory for logs (unique per test session)
    log_dir = tmp_path_factory.mktemp("logs")
    # Use a unique log file name (e.g. based on process id and timestamp)
    log_file = log_dir / f"log_{os.getpid()}_{int(os.times()[4])}.log"

    # Remove any existing file handlers on the root logger.
    logger = logging.getLogger()
    for handler in logger.handlers[:]:
        if isinstance(handler, logging.FileHandler):
            logger.removeHandler(handler)

    # Create a new FileHandler in write mode so it doesn't append.
    file_handler = logging.FileHandler(log_file, mode="w", encoding="utf-8")
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.setLevel(logging.DEBUG)

    # Optionally, print the log file location for debugging.
    print(f"\nNew log file for test: {log_file}\n")

    yield

    # Cleanup: remove our file handler so that subsequent tests (if any)
    # can set up their own log file.
    logger.removeHandler(file_handler)
