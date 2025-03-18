"""Environment detection utilities for dual-mode operation."""

import os
from pathlib import Path

from the_aichemist_codex.backend.config.settings import determine_project_root


def is_development_mode() -> bool:
    """
    Detect if running in development mode (not installed as package).

    This checks if we're running from source directories or as an installed package.

    Returns:
        bool: True if running from source, False if installed as package
    """
    # Check explicit environment variable first
    if os.environ.get("AICHEMIST_DEV_MODE"):
        return True

    # Check if running from source directory structure
    module_path = Path(__file__).resolve()
    src_parent = "src"

    # If we're in a src/the_aichemist_codex structure, we're in development mode
    return src_parent in module_path.parts


def get_import_mode() -> str:
    """
    Determine how the package was imported.

    Returns:
        str: "package" if installed and imported as a package,
             "standalone" if running from source,
             "editable" if installed in development/editable mode
    """
    if is_development_mode():
        return "standalone"

    # Check for editable install
    try:
        import importlib.metadata
        import sys
        from importlib.util import find_spec

        # More reliable way to detect editable installs
        # If the package is installed in editable mode, the spec will point to the source directory
        spec = find_spec("the_aichemist_codex")
        if spec and spec.origin:
            origin_path = Path(spec.origin).resolve()
            if "site-packages" not in str(origin_path) and "src" in origin_path.parts:
                return "editable"
    except (ImportError, ModuleNotFoundError):
        pass

    return "package"


def get_project_root() -> Path:
    """
    Get the project root directory regardless of execution context.

    This function builds on top of determine_project_root() from settings
    but adds additional logic specific to package vs. standalone mode.

    Returns:
        Path: The project root directory
    """
    # Use the existing project root detection
    return determine_project_root()


def get_package_dir() -> Path:
    """
    Get the package installation directory when running as an installed package.

    Returns:
        Path: The package installation directory
    """
    # If in development mode, return the src/the_aichemist_codex directory
    if is_development_mode():
        return Path(__file__).resolve().parents[2]

    # If installed, return the site-packages directory for the package
    import the_aichemist_codex

    return Path(the_aichemist_codex.__file__).resolve().parent
