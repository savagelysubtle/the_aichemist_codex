#!/usr/bin/env python3
"""
Code Quality Automation Script for The Aichemist Codex.

This script automates various code quality tasks like formatting,
import organization, and linting to help maintain consistent code quality.

Usage:
    python scripts/code_quality.py [--format] [--lint] [--typecheck] [--all] [--fix]
"""

import argparse
import subprocess
import sys
from pathlib import Path


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Automate code quality tasks for The Aichemist Codex"
    )
    parser.add_argument(
        "--format", action="store_true", help="Format code with ruff format"
    )
    parser.add_argument("--lint", action="store_true", help="Run ruff linting")
    parser.add_argument(
        "--typecheck", action="store_true", help="Run mypy type checking"
    )
    parser.add_argument(
        "--all", action="store_true", help="Run all code quality checks"
    )
    parser.add_argument(
        "--fix", action="store_true", help="Attempt to fix issues automatically"
    )
    parser.add_argument(
        "--path",
        type=str,
        default="src",
        help="Path to check (default: src)",
    )
    return parser.parse_args()


def run_command(command, description):
    """Run a command and print its output."""
    print(f"\n=== Running {description} ===\n")
    result = subprocess.run(command, shell=True, text=True, capture_output=True)
    print(result.stdout)
    if result.stderr:
        print(f"Errors:\n{result.stderr}")
    return result.returncode


def format_code(path, fix=False):
    """Format code with ruff format."""
    cmd = f"ruff format {path}"
    return run_command(cmd, "code formatting")


def lint_code(path, fix=False):
    """Run ruff linting."""
    fix_arg = "--fix" if fix else ""
    cmd = f"ruff check {fix_arg} {path}"
    return run_command(cmd, "code linting")


def check_types(path):
    """Run mypy type checking."""
    cmd = f"mypy {path}"
    return run_command(cmd, "type checking")


def organize_imports(path, fix=False):
    """Organize imports with ruff."""
    fix_arg = "--fix" if fix else ""
    cmd = f"ruff check --select I {fix_arg} {path}"
    return run_command(cmd, "import organization")


def main():
    """Main function."""
    args = parse_args()
    path = args.path

    # Verify that the path exists
    if not Path(path).exists():
        print(f"Error: Path '{path}' does not exist.")
        return 1

    exit_code = 0

    # If no specific actions are specified and --all is not set,
    # default to running everything in check mode (no fixes)
    if not (args.format or args.lint or args.typecheck or args.all):
        args.all = True
        args.fix = False
        print("No specific actions specified. Running all checks without fixing.")

    if args.format or args.all:
        format_result = format_code(path, args.fix)
        exit_code = exit_code or format_result

    if args.lint or args.all:
        # Run import organization first
        import_result = organize_imports(path, args.fix)
        exit_code = exit_code or import_result

        # Then run general linting
        lint_result = lint_code(path, args.fix)
        exit_code = exit_code or lint_result

    if args.typecheck or args.all:
        type_result = check_types(path)
        exit_code = exit_code or type_result

    # Print summary
    if exit_code == 0:
        print("\n✅ All checks passed successfully!")
    else:
        print(
            "\n❌ Some checks failed. Please review the output above and fix the issues."
        )
        if not args.fix:
            print("Try running with --fix to automatically fix some issues.")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
