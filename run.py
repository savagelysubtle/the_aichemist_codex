#!/usr/bin/env python3
"""
Development mode runner for The Aichemist Codex.

This script provides a convenient way to run the application in development mode
without installing it. It sets up the Python path correctly and configures
environment variables for development.

Usage:
    python run.py [command] [args...]

Examples:
    python run.py tree data/
    python run.py summarize src/
    python run.py data validate
"""

import os
import sys
from pathlib import Path

# Add src to Python path to enable imports
src_path = Path(__file__).resolve().parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Mark as development mode
os.environ["AICHEMIST_DEV_MODE"] = "1"

# Import CLI only after path setup
from the_aichemist_codex.backend.cli import main

if __name__ == "__main__":
    # Print development mode banner
    print("\033[1;36m" + "=" * 70)
    print(" The Aichemist Codex - Development Mode ")
    print("=" * 70 + "\033[0m")

    # Run the CLI
    sys.exit(main())
