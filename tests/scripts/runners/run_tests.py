#!/usr/bin/env python
"""
Main test runner for The AIchemist Codex project.

This script provides a convenient way to run tests with different options.
Run this script directly to execute all tests, or use command-line arguments
to run specific test categories.
"""

import argparse
import os
import subprocess
import sys


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Run tests for The AIchemist Codex project"
    )
    parser.add_argument("--unit", action="store_true", help="Run only unit tests")
    parser.add_argument(
        "--integration", action="store_true", help="Run only integration tests"
    )
    parser.add_argument(
        "--metadata", action="store_true", help="Run only metadata tests"
    )
    parser.add_argument("--tagging", action="store_true", help="Run only tagging tests")
    parser.add_argument("--search", action="store_true", help="Run only search tests")
    parser.add_argument("--cli", action="store_true", help="Run only CLI tests")
    parser.add_argument("--simple", action="store_true", help="Run only simple tests")
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Run tests in verbose mode"
    )
    parser.add_argument(
        "--coverage", action="store_true", help="Generate coverage report"
    )
    return parser.parse_args()


def run_tests(args):
    """Run tests based on command-line arguments."""
    # Determine the base directory
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Build the pytest command
    cmd = [sys.executable, "-m", "pytest"]

    # Add verbosity if requested
    if args.verbose:
        cmd.append("-v")

    # Add coverage if requested
    if args.coverage:
        cmd.extend(["--cov=backend", "--cov-report=term", "--cov-report=html"])

    # Add markers based on arguments
    markers = []
    if args.unit:
        markers.append("unit")
    if args.integration:
        markers.append("integration")
    if args.metadata:
        markers.append("metadata")
    if args.tagging:
        markers.append("tagging")
    if args.search:
        markers.append("search")
    if args.cli:
        markers.append("cli")

    # Handle the simple tests case separately
    if args.simple:
        # Use the correct path relative to the backend directory
        cmd.append("tests/unit/simple")
    elif markers:
        # Combine markers with OR logic
        marker_expr = " or ".join(markers)
        cmd.extend(["-m", marker_expr])

    # Run the tests
    print(f"Running command: {' '.join(cmd)}")
    return subprocess.run(cmd, cwd=base_dir)


def main():
    """Main entry point."""
    args = parse_args()

    # If no specific test category is selected, run all tests
    if not any(
        [
            args.unit,
            args.integration,
            args.metadata,
            args.tagging,
            args.search,
            args.cli,
            args.simple,
        ]
    ):
        print("Running all tests...")

    # Run the tests
    result = run_tests(args)

    # Return the exit code
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
