"""Main execution script for The Aichemist Codex with Windows Tkinter GUI."""

import logging
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

# ✅ Ensure correct package resolution
sys.path.append(str(Path(__file__).resolve().parent))

from aichemist_codex.file_manager.file_tree import generate_file_tree
from aichemist_codex.project_reader.code_summary import summarize_project

logger = logging.getLogger(__name__)


def select_directory(prompt: str) -> Path:
    """Open a GUI file dialog to let the user select a directory."""
    root = tk.Tk()
    root.withdraw()
    folder_selected = filedialog.askdirectory(title=prompt)

    if not folder_selected:
        messagebox.showinfo("No Selection", "No directory selected. Exiting.")
        return None  # Return None to allow cancellation

    return Path(folder_selected).resolve()


def ensure_directory_exists(directory: Path):
    """Ensure the output directory exists."""
    try:
        directory.mkdir(parents=True, exist_ok=True)
        logger.info(f"Output directory ensured: {directory}")
    except Exception as e:
        logger.error(f"Error ensuring output directory {directory}: {e}")
        messagebox.showerror("Error", f"Failed to create output directory: {e}")


def run_analysis():
    """Handles file tree generation and code summarization via Tkinter GUI."""
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

    logger.info(f"Analyzing directory: {input_directory}")

    try:
        # ✅ Generate File Tree
        logger.info(f"Generating file tree for {input_directory}")
        generate_file_tree(input_directory, output_tree_file)
        logger.info(f"File tree saved to {output_tree_file}")

        # ✅ Run Code Summarization
        logger.info(f"Summarizing code in {input_directory}")
        summarize_project(input_directory, output_md_file, output_json_file)

        # ✅ Show Completion Message
        messagebox.showinfo(
            "Success",
            f"Analysis completed!\n\nFile Tree: {output_tree_file}\nSummary (JSON): {output_json_file}\nSummary (Markdown): {output_md_file}",
        )
        logger.info("Analysis completed successfully.")

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        messagebox.showerror("Error", f"An error occurred: {e}")


if __name__ == "__main__":
    run_analysis()
