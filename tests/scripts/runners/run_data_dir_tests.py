#!/usr/bin/env python
"""
Helper script to run data directory tests.

This script runs the data directory tests using pytest.
"""

import os
import sys
from pathlib import Path

import pytest


def main():
    """Run the data directory tests."""
    # Get the absolute path to the backend directory
    backend_dir = Path(__file__).resolve().parent.parent

    # Add the backend directory to sys.path
    sys.path.insert(0, str(backend_dir))

    # Set the working directory to the backend directory
    os.chdir(backend_dir)

    # Get the path to the data directory tests
    test_path = "tests/utils/test_data_dir.py"

    # Run the tests
    args = ["-v", test_path]
    print(f"Running tests: {' '.join(args)}")
    result = pytest.main(args)

    # Return the test result as the exit code
    return result


if __name__ == "__main__":
    sys.exit(main())
