import logging
import os
import shutil
import sys
from collections.abc import Generator
from pathlib import Path

import pytest

# Calculate the absolute path to the backend directory.
# The structure is /project_root/backend, not /project_root/backend/backend
# So we just need to go one level up from the tests directory
BACKEND_DIR = Path(__file__).resolve().parent.parent
BACKEND_SRC_DIR = BACKEND_DIR / "src"

# Dynamically add each package under backend/src to sys.path if it exists
if BACKEND_SRC_DIR.exists():
    for subdir in BACKEND_SRC_DIR.iterdir():
        if subdir.is_dir() and (subdir / "__init__.py").exists():
            sys.path.insert(0, str(subdir))
else:
    # If no src directory, then try to find packages directly under backend
    for subdir in BACKEND_DIR.iterdir():
        if (
            subdir.is_dir()
            and (subdir / "__init__.py").exists()
            and subdir.name != "tests"
        ):
            sys.path.insert(0, str(subdir))

# Also add the main backend directory itself to sys.path
sys.path.insert(0, str(BACKEND_DIR))

# Root directory of the project
ROOT_DIR = Path(__file__).resolve().parent.parent

# Directory to store temporary logs index
TMP_LOG_INDEX = ROOT_DIR / "data" / "tmp_logs_index.txt"

# Ensure data directory exists
data_dir = ROOT_DIR / "data"
data_dir.mkdir(exist_ok=True)


@pytest.fixture(autouse=True)
def new_log_file(tmp_path: Path) -> Generator[None]:
    """
    Resets the root logger's FileHandler before each test so that
    a new log file is used.
    This prevents log messages from accumulating across tests.
    """
    # Create a common parent directory for test logs
    test_logs_root = ROOT_DIR / "data" / "test_logs"
    test_logs_root.mkdir(parents=True, exist_ok=True)

    # Create a new temporary directory for logs (unique per test session)
    # Use a consistent naming pattern with timestamps
    import time

    timestamp = int(time.time())
    pid = os.getpid()
    log_dir = test_logs_root / f"test_logs_{timestamp}_{pid}"
    log_dir.mkdir(parents=True, exist_ok=True)

    # Use a unique log file name
    log_file = log_dir / "test.log"

    # Record this log directory for cleanup
    with open(TMP_LOG_INDEX, "a") as index_file:
        index_file.write(f"{log_dir}\n")

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

    # Try to clean up old test log directories
    _cleanup_old_test_logs()


def _cleanup_old_test_logs() -> None:
    """Clean up old test log directories that are over 24 hours old."""
    try:
        if not TMP_LOG_INDEX.exists():
            return

        import time

        current_time = time.time()
        day_in_seconds = 60 * 60 * 24

        # Read the index file
        with open(TMP_LOG_INDEX) as index_file:
            log_dirs = [line.strip() for line in index_file.readlines()]

        # Filter out non-existent directories and collect ones to delete
        dirs_to_keep = []
        for dir_path in log_dirs:
            path = Path(dir_path)
            if not path.exists():
                continue

            # Check if the directory is older than 24 hours
            try:
                dir_time = path.stat().st_mtime
                if (current_time - dir_time) > day_in_seconds:
                    shutil.rmtree(path, ignore_errors=True)
                else:
                    dirs_to_keep.append(dir_path)
            except Exception:
                # Keep the directory in the list if we couldn't check its age
                dirs_to_keep.append(dir_path)

        # Update the index file with remaining directories
        with open(TMP_LOG_INDEX, "w") as index_file:
            for dir_path in dirs_to_keep:
                index_file.write(f"{dir_path}\n")
    except Exception as e:
        print(f"Error cleaning up test logs: {e}")
