"""
Command-line interface for The AIChemist Codex.

This module provides a command-line interface to the application's functionality,
using our registry-based architecture to avoid circular dependencies.
"""

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path

from .bootstrap import bootstrap
from .registry import Registry
from .tools.validate_data_dir import validate_data_directory

# Set up logging
logger = logging.getLogger(__name__)


def validate_directory(directory: str) -> Path:
    """
    Validate that a directory exists and is accessible.

    Args:
        directory: Directory path to validate

    Returns:
        Path object for the directory

    Raises:
        ValueError: If the directory does not exist
    """
    path = Path(directory).resolve()
    if not path.exists():
        raise ValueError(f"Directory does not exist: {path}")
    if not path.is_dir():
        raise ValueError(f"Path is not a directory: {path}")
    if not os.access(path, os.R_OK | os.W_OK):
        raise ValueError(f"Directory is not accessible: {path}")
    return path


async def analyze_directory(
    input_directory: Path,
    output_directory: Path,
    max_depth: int = 10,
    include_metadata: bool = False,
) -> None:
    """
    Analyze a directory and generate reports.

    Args:
        input_directory: Directory to analyze
        output_directory: Directory to save reports
        max_depth: Maximum depth for file tree generation
        include_metadata: Whether to include metadata in reports
    """
    # Get registry
    registry = Registry.get_instance()

    # Get services
    file_tree = registry.file_tree
    dir_manager = registry.directory_manager
    file_writer = registry.file_writer

    # Ensure output directory exists
    await dir_manager.ensure_directory_exists(str(output_directory))

    # Generate outputs
    project_name = input_directory.name
    output_tree_file = output_directory / f"{project_name}_file_tree.json"

    logger.info(f"Analyzing directory: {input_directory}")

    # Generate file tree
    logger.info(f"Generating file tree for {input_directory}")
    tree_data = await file_tree.get_tree(str(input_directory), max_depth=max_depth)

    # Save tree data
    await file_writer.write_json(str(output_tree_file), tree_data)
    logger.info(f"File tree saved to {output_tree_file}")

    if include_metadata:
        # In the future, add metadata analysis here
        pass

    logger.info("Analysis completed successfully.")


def setup_parser() -> argparse.ArgumentParser:
    """
    Set up the command-line parser.

    Returns:
        Configured argument parser
    """
    parser = argparse.ArgumentParser(
        description="The AIChemist Codex - Code Analysis Tool"
    )

    # Add global arguments
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose logging"
    )

    # Add subcommands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze a directory")
    analyze_parser.add_argument("input_directory", help="Directory to analyze")
    analyze_parser.add_argument(
        "-o", "--output", help="Output directory (defaults to INPUT_DIRECTORY/analysis)"
    )
    analyze_parser.add_argument(
        "-d",
        "--depth",
        type=int,
        default=10,
        help="Maximum depth for file tree (default: 10)",
    )
    analyze_parser.add_argument(
        "-m", "--metadata", action="store_true", help="Include metadata in analysis"
    )

    # Validate command
    subparsers.add_parser("validate", help="Validate data directory configuration")

    return parser


async def handle_analyze_command(args) -> int:
    """
    Handle the analyze command.

    Args:
        args: Command-line arguments

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        # Validate input directory
        input_dir = validate_directory(args.input_directory)

        # Determine output directory
        if args.output:
            output_dir = Path(args.output).resolve()
        else:
            output_dir = input_dir / "analysis"

        # Run analysis
        await analyze_directory(
            input_dir, output_dir, max_depth=args.depth, include_metadata=args.metadata
        )

        return 0
    except ValueError as e:
        logger.error(f"Invalid directory: {e}")
        return 1
    except Exception as e:
        logger.error(f"Error during analysis: {e}")
        return 1


def handle_validate_command(args) -> int:
    """
    Handle the validate command.

    Args:
        args: Command-line arguments

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        if validate_data_directory():
            logger.info("Data directory validation passed!")
            return 0
        else:
            logger.error("Data directory validation failed!")
            return 1
    except Exception as e:
        logger.error(f"Error during validation: {e}")
        return 1


async def main_async() -> int:
    """
    Main asynchronous execution function.

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    # Parse command-line arguments
    parser = setup_parser()
    args = parser.parse_args()

    # Configure logging level
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    # Initialize application
    bootstrap()

    # Execute command
    if args.command == "analyze":
        return await handle_analyze_command(args)
    elif args.command == "validate":
        return handle_validate_command(args)
    else:
        parser.print_help()
        return 0


def main() -> int:
    """
    Main entry point for the CLI.

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        return asyncio.run(main_async())
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        return 130
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
