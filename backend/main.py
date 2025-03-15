"""Main execution script for The Aichemist Codex with Windows Tkinter GUI."""

import asyncio
import logging
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

# Ensure correct package resolution
sys.path.append(str(Path(__file__).resolve().parent))

# Set up logging early
from backend.config.logging_config import setup_logging

setup_logging()

from backend.file_manager.file_tree import generate_file_tree
from backend.ingest.reader import generate_digest
from backend.project_reader.code_summary import summarize_project

logger = logging.getLogger(__name__)


def select_directory(prompt: str) -> Path | None:
    """Open a GUI file dialog to let the user select a directory."""
    root = tk.Tk()
    root.withdraw()
    folder_selected = filedialog.askdirectory(title=prompt)
    if not folder_selected:
        messagebox.showinfo("No Selection", "No directory selected. Exiting.")
        return None  # Allow cancellation by returning None
    return Path(folder_selected).resolve()


def ensure_directory_exists(directory: Path):
    """Ensure the output directory exists."""
    try:
        directory.mkdir(parents=True, exist_ok=True)
        logger.info(f"Output directory ensured: {directory}")
    except Exception as e:
        logger.error(f"Error ensuring output directory {directory}: {e}")
        messagebox.showerror("Error", f"Failed to create output directory: {e}")


async def run_analysis():
    """Handles file tree generation, code summarization, and full project ingestion via the Tkinter GUI."""
    input_directory = select_directory("Select the directory to analyze")
    if not input_directory:
        return  # User cancelled

    output_directory = select_directory("Select the output directory")
    if not output_directory:
        output_directory = input_directory.parent  # Default output directory

    ensure_directory_exists(output_directory)

    project_name = input_directory.name
    output_json_file = output_directory / f"{project_name}_code_summary.json"
    output_md_file = output_directory / f"{project_name}_code_summary.md"
    output_tree_file = output_directory / f"{project_name}_file_tree.json"
    output_digest_file = output_directory / f"{project_name}_digest.txt"

    logger.info(f"Analyzing directory: {input_directory}")

    try:
        # Generate File Tree
        logger.info(f"Generating file tree for {input_directory}")
        await generate_file_tree(input_directory, max_depth=10)
        logger.info(f"File tree saved to {output_tree_file}")

        # Run Code Summarization
        logger.info(f"Summarizing code in {input_directory}")
        await summarize_project(input_directory, output_md_file, output_json_file)

        # Generate Ingestible Digest using the new ingestion module
        logger.info(f"Generating project digest for {input_directory}")
        digest = generate_digest(
            input_directory,
            options={
                "include_patterns": {"*"},  # Include all file types
                "ignore_patterns": set(),  # No ignore patterns for now
                "include_notebook_output": True,  # Include outputs for notebooks
            },
        )
        output_digest_file.write_text(digest, encoding="utf-8")
        logger.info(f"Digest saved to {output_digest_file}")

        # Show a message indicating successful analysis
        messagebox.showinfo(
            "Success",
            f"Analysis completed!\n\n"
            f"File Tree: {output_tree_file}\n"
            f"Summary (JSON): {output_json_file}\n"
            f"Summary (Markdown): {output_md_file}\n"
            f"Digest: {output_digest_file}",
        )
        logger.info("Analysis completed successfully.")

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        messagebox.showerror("Error", f"An error occurred: {e}")


if __name__ == "__main__":
    asyncio.run(run_analysis())
