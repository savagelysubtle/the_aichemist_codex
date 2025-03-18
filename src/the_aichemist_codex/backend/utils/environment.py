"""Environment detection and configuration utilities."""

import os
from pathlib import Path


def is_development_mode() -> bool:
    """
    Detect if running in development mode.

    Development mode is detected by:
    1. Presence of AICHEMIST_DEV_MODE environment variable
    2. Being run directly from the source directory
    3. Being run from a git clone (presence of .git directory)

    Returns:
        bool: True if running in development mode, False otherwise
    """
    # Check for explicit development mode env var
    if os.environ.get("AICHEMIST_DEV_MODE"):
        return True

    # Check if running directly from source
    try:
        module_path = Path(__file__).resolve().parent.parent.parent.parent
        src_path = module_path.parent

        # Check for setup.py or pyproject.toml in parent directory
        if (src_path / "pyproject.toml").exists():
            # Check for .git folder to distinguish between installed and development
            if (src_path.parent / ".git").exists():
                return True
    except Exception:
        pass

    return False


def get_app_config_dir() -> Path:
    """
    Get the application configuration directory.

    In development mode, this is a local directory in the project.
    In installed mode, this is in the user's home directory.

    Returns:
        Path: Path to the configuration directory
    """
    if is_development_mode():
        # Use a local config directory for development
        module_path = Path(__file__).resolve().parent.parent.parent.parent
        return module_path.parent / "config"
    else:
        # Use platform-specific config locations for installed mode
        import platformdirs

        return Path(platformdirs.user_config_dir("aichemist-codex"))


def get_app_data_dir() -> Path:
    """
    Get the application data directory.

    In development mode, this is a local directory in the project.
    In installed mode, this is in the user's home directory.

    Returns:
        Path: Path to the data directory
    """
    if is_development_mode():
        # Use a local data directory for development
        module_path = Path(__file__).resolve().parent.parent.parent.parent
        return module_path.parent / "data"
    else:
        # Use platform-specific data locations for installed mode
        import platformdirs

        return Path(platformdirs.user_data_dir("aichemist-codex"))


def get_app_cache_dir() -> Path:
    """
    Get the application cache directory.

    In development mode, this is a local directory in the project.
    In installed mode, this is in the user's home directory.

    Returns:
        Path: Path to the cache directory
    """
    if is_development_mode():
        # Use a local cache directory for development
        module_path = Path(__file__).resolve().parent.parent.parent.parent
        return module_path.parent / "cache"
    else:
        # Use platform-specific cache locations for installed mode
        import platformdirs

        return Path(platformdirs.user_cache_dir("aichemist-codex"))


def get_app_log_dir() -> Path:
    """
    Get the application log directory.

    In development mode, this is a local directory in the project.
    In installed mode, this is in the user's home directory.

    Returns:
        Path: Path to the log directory
    """
    if is_development_mode():
        # Use a local log directory for development
        module_path = Path(__file__).resolve().parent.parent.parent.parent
        return module_path.parent / "logs"
    else:
        # Use platform-specific log locations for installed mode
        import platformdirs

        return Path(platformdirs.user_log_dir("aichemist-codex"))
