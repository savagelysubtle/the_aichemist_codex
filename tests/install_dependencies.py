#!/usr/bin/env python
"""
Script to install missing dependencies required for tests.

This script detects and installs missing Python packages that are required
for running the tests in the project.
"""

import subprocess
import sys


def install_package(package_name):
    """Install a Python package using pip."""
    try:
        print(f"Installing {package_name}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error installing {package_name}: {e}")
        return False


def main():
    """Main function to install dependencies."""
    print("Checking and installing missing dependencies...")

    # List of dependencies that might be missing based on test errors
    dependencies = [
        "mutagen",  # For audio file metadata extraction
        "pytest",
        "pytest-asyncio",
        "pytest-cov",
        "pytest-mock",
        "scipy",
        "numpy",
        "pydub",
    ]

    # Install each dependency
    installed_count = 0
    failed_count = 0

    for package in dependencies:
        if install_package(package):
            installed_count += 1
        else:
            failed_count += 1

    print(f"\nInstalled {installed_count} packages.")
    if failed_count > 0:
        print(f"Failed to install {failed_count} packages.")


if __name__ == "__main__":
    main()
