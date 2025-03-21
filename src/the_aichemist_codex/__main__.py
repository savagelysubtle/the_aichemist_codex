"""Main entry point for direct execution in both package and standalone modes."""

import sys
from pathlib import Path

from the_aichemist_codex.backend.cli import main
from the_aichemist_codex.backend.utils.environment import is_development_mode


def setup_environment():
    """Set up the environment for dual-mode execution."""
    # Set development mode environment variable if detected
    if is_development_mode():
        import os

        os.environ.setdefault("AICHEMIST_DEV_MODE", "1")

        # Add src directory to path if needed in development mode
        src_path = Path(__file__).resolve().parent.parent
        if str(src_path) not in sys.path:
            sys.path.insert(0, str(src_path))


if __name__ == "__main__":
    setup_environment()
    sys.exit(main())
