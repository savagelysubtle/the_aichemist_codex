"""
Main execution script for The AIChemist Codex.

This is the main entry point for the application and supports both
GUI and CLI modes.
"""

import asyncio
import logging
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

# Bootstrap the application
from .bootstrap import bootstrap
from .registry import Registry

# Set up logging
logger = logging.getLogger(__name__)


def setup_application():
    """Initialize the application and set up dependencies."""
    bootstrap()
    logger.info("Application initialized")


def select_directory(prompt: str) -> Path | None:
    """
    Open a GUI file dialog to let the user select a directory.

    Args:
        prompt: Message to display in the dialog

    Returns:
        Selected directory path or None if cancelled
    """
    root = tk.Tk()
    root.withdraw()
    folder_selected = filedialog.askdirectory(title=prompt)
    if not folder_selected:
        messagebox.showinfo("No Selection", "No directory selected. Exiting.")
        return None  # Allow cancellation by returning None
    return Path(folder_selected).resolve()


async def ensure_directory_exists(directory: Path) -> bool:
    """
    Ensure the specified directory exists.

    Args:
        directory: The directory to ensure

    Returns:
        True if successful, False otherwise
    """
    try:
        # Use our DirectoryManager from the registry
        registry = Registry.get_instance()
        dir_manager = registry.directory_manager

        # Convert Path to string for the directory manager
        await dir_manager.ensure_directory_exists(str(directory))
        logger.info(f"Output directory ensured: {directory}")
        return True
    except Exception as e:
        logger.error(f"Error ensuring output directory {directory}: {e}")
        messagebox.showerror("Error", f"Failed to create output directory: {e}")
        return False


async def run_analysis():
    """
    Run the full analysis pipeline with GUI file selection.

    This handles:
    1. Directory selection
    2. File tree generation
    3. Code summarization
    4. Project digest generation
    """
    # Initialize the application
    setup_application()

    # Get the necessary services from registry
    registry = Registry.get_instance()
    file_tree = registry.file_tree
    # In future versions, we'll add more services here

    # Select directories via GUI
    input_directory = select_directory("Select the directory to analyze")
    if not input_directory:
        return  # User cancelled

    output_directory = select_directory("Select the output directory")
    if not output_directory:
        output_directory = input_directory.parent  # Default output directory

    # Ensure the output directory exists
    success = await ensure_directory_exists(output_directory)
    if not success:
        return

    project_name = input_directory.name
    output_tree_file = output_directory / f"{project_name}_file_tree.json"

    logger.info(f"Analyzing directory: {input_directory}")

    try:
        # Generate File Tree
        logger.info(f"Generating file tree for {input_directory}")
        tree_data = await file_tree.get_tree(str(input_directory), max_depth=10)

        # Save the tree data using our FileWriter
        writer = registry.file_writer
        await writer.write_json(str(output_tree_file), tree_data)
        logger.info(f"File tree saved to {output_tree_file}")

        # Show a message indicating successful analysis
        messagebox.showinfo(
            "Success", f"Analysis completed!\n\nFile Tree: {output_tree_file}\n"
        )
        logger.info("Analysis completed successfully.")

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        messagebox.showerror("Error", f"An error occurred: {e}")


def main():
    """
    Main entry point for the application.

    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        asyncio.run(run_analysis())
        return 0
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
