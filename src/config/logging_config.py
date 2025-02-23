import logging
import os
import sys


def setup_logging(
    log_dir="logs", log_file_name="file_events.log", log_level=logging.INFO
):
    """
    Sets up centralized logging for the application.

    Args:
        log_dir (str): Directory where logs will be stored.
        log_file_name (str): Name of the log file.
        log_level (int): Logging level (default: logging.INFO).
    """
    # Ensure log directory exists
    os.makedirs(log_dir, exist_ok=True)

    # Define log file path
    log_file_path = os.path.join(log_dir, log_file_name)

    # Configure logging settings
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file_path),  # Log to file
            logging.StreamHandler(sys.stdout),  # Also log to console
        ],
    )

    logging.info(f"Logging initialized. Log file: {log_file_path}")
    return log_file_path
