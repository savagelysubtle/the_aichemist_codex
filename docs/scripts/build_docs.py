#!/usr/bin/env python
"""
Automated Sphinx Documentation Builder for The Aichemist Codex.

This script automates the entire documentation build process:
1. Generates API documentation with generate_api_docs.py
2. Builds HTML documentation with Sphinx
3. Provides options for other formats (PDF, EPUB)
"""

import argparse
import importlib.util
import os
import platform
import shlex
import subprocess
import sys
from pathlib import Path

# Import generate_api_docs
generate_api_docs_path = Path(__file__).resolve().parent / "generate_api_docs.py"
spec = importlib.util.spec_from_file_location(
    "generate_api_docs", generate_api_docs_path
)
if spec is None:
    print(f"Error: Could not find generate_api_docs.py at {generate_api_docs_path}")
    sys.exit(1)

generate_api_docs = importlib.util.module_from_spec(spec)
if spec.loader is None:
    print("Error: Module loader is None")
    sys.exit(1)

spec.loader.exec_module(generate_api_docs)


def run_sphinx_command(command: str, description: str | None = None) -> bool:
    """Run a sphinx-build command and print its output.

    Args:
        command: The sphinx command to run (trusted input only)
        description: Optional description of the command

    Returns:
        bool: Whether the command succeeded
    """
    if description:
        print(f"\n{description}...")

    try:
        # For Windows, we need to be careful with command-line arguments
        if platform.system() == "Windows":
            # Parse the command carefully preserving all arguments
            if command.startswith("sphinx-build -M"):
                # Handle the special case for sphinx-build -M format sourcedir outputdir
                parts = command.split(
                    " ", 3
                )  # Split into: ["sphinx-build", "-M", "format", "sourcedir outputdir"]
                if len(parts) >= 4:
                    # Further split the last part into sourcedir and outputdir
                    dir_parts = parts[3].strip().split(" ", 1)
                    if len(dir_parts) == 2:
                        args = [
                            parts[0],
                            parts[1],
                            parts[2],
                            dir_parts[0],
                            dir_parts[1],
                        ]
                    else:
                        # Something is wrong with the format
                        raise ValueError(f"Unexpected command format: {command}")
                else:
                    raise ValueError(f"Unexpected command format: {command}")
            else:
                # For other commands just use regular parsing
                args = shlex.split(command)
        else:
            # On Unix-like systems, use shlex
            args = shlex.split(command)

        # Safety check - ensure this is a sphinx-build command
        if not args[0].startswith("sphinx-build"):
            raise ValueError(f"Unsupported command: {args[0]}")

        # Run the sphinx command with arguments
        print(f"Running command: {' '.join(args)}")
        process = subprocess.run(  # noqa: S603
            args,
            check=True,
            capture_output=True,
            text=True,
        )
        print(process.stdout)
        if process.stderr:
            print(f"Warnings/errors:\n{process.stderr}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        print(f"Command output:\n{e.stdout}")
        print(f"Command errors:\n{e.stderr}")
        return False
    except ValueError as e:
        print(f"Error: {e}")
        return False


def build_docs(output_format: str = "html", clean: bool = False) -> None:
    """
    Build documentation using Sphinx.

    Args:
        output_format: Format to build (html, pdf, epub)
        clean: Whether to clean the build directory first
    """
    # Get the docs directory (parent of the scripts directory)
    docs_dir = Path(__file__).resolve().parent.parent
    build_dir = docs_dir / "_build"

    # Create build directory if it doesn't exist
    os.makedirs(build_dir, exist_ok=True)

    # Set up the commands
    commands: list[tuple[str, str]] = []

    # Convert paths to strings with proper escaping for command line
    docs_dir_str = str(docs_dir).replace("\\", "/")
    build_dir_str = str(build_dir).replace("\\", "/")

    # Clean build if requested
    if clean:
        commands.append(
            (
                f"sphinx-build -M clean {docs_dir_str} {build_dir_str}",
                "Cleaning build directory",
            )
        )

    # Generate API documentation
    print("Generating API documentation...")
    generate_api_docs.main()

    # Build documentation
    build_command = f"sphinx-build -M {output_format} {docs_dir_str} {build_dir_str}"
    commands.append((build_command, f"Building {output_format} documentation"))

    # Run all commands
    success = True
    for cmd, desc in commands:
        if not run_sphinx_command(cmd, desc):
            success = False
            break

    if success:
        output_path = build_dir / output_format
        print(f"\n✅ Documentation built successfully! Output is in {output_path}")

        # For HTML, print the index.html path
        if output_format == "html":
            index_path = output_path / "index.html"
            print(f"Open this file to view your documentation: {index_path}")
    else:
        print("\n❌ Documentation build failed. See errors above.")
        sys.exit(1)


def main() -> None:
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Build Sphinx documentation for The Aichemist Codex."
    )
    parser.add_argument(
        "--format",
        choices=["html", "pdf", "epub"],
        default="html",
        help="Output format (default: html)",
    )
    parser.add_argument(
        "--clean", action="store_true", help="Clean the build directory before building"
    )

    args = parser.parse_args()

    print("=" * 80)
    print("The Aichemist Codex Documentation Builder")
    print("=" * 80)

    build_docs(args.format, args.clean)


if __name__ == "__main__":
    main()
