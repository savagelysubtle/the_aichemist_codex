import argparse
import json
import logging
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

from file_manager.file_tree import generate_file_tree
from output.markdown_writer import save_as_markdown

# ✅ Fixed imports based on new project structure
from project_reader.code_summary import summarize_code
from utils.validator import get_project_name

# ✅ Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def select_directory(prompt: str) -> Path:
    """Open a GUI file dialog to let the user select a directory."""
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    folder_selected = filedialog.askdirectory(title=prompt)

    if not folder_selected:
        messagebox.showinfo("No Selection", "No directory selected. Exiting.")
        exit(1)  # ✅ Gracefully exit if no directory is selected

    return Path(folder_selected).resolve()


def main(
    directory: Path,
    output_directory: Path,
    generate_tree: bool,
    summarize_codebase: bool,
):
    """Runs file tree and/or code summary analysis."""
    if not directory.exists():
        logging.error(f"Directory '{directory}' does not exist.")
        messagebox.showerror("Error", f"Directory '{directory}' does not exist.")
        return

    if not output_directory.exists():
        logging.error(f"Output directory '{output_directory}' does not exist.")
        messagebox.showerror(
            "Error", f"Output directory '{output_directory}' does not exist."
        )
        return

    project_name = get_project_name(directory)

    if generate_tree:
        file_tree_output = output_directory / f"{project_name}_file_tree.json"
        file_tree = generate_file_tree(directory)
        file_tree_output.write_text(json.dumps(file_tree, indent=4), encoding="utf-8")
        logging.info(f"File tree saved to {file_tree_output}")

        markdown_output_file = output_directory / f"{project_name}_file_tree.md"
        save_as_markdown(markdown_output_file, file_tree, {}, "File Tree")

    if summarize_codebase:
        code_summary_output = output_directory / f"{project_name}_code_summary.json"
        code_summaries = summarize_code(directory)
        code_summary_output.write_text(
            json.dumps(code_summaries, indent=4), encoding="utf-8"
        )
        logging.info(f"Code summary saved to {code_summary_output}")

        markdown_output_file = output_directory / f"{project_name}_code_summary.md"
        save_as_markdown(markdown_output_file, code_summaries, {}, "Code Summary")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Analyze a directory for file structure and code summaries."
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Use GUI to select input and output directories.",
    )
    parser.add_argument(
        "directory",
        nargs="?",
        type=Path,
        help="Path to the directory to analyze (optional if using GUI).",
    )
    parser.add_argument(
        "output_directory",
        nargs="?",
        type=Path,
        help="Path to save output files (optional if using GUI).",
    )
    parser.add_argument(
        "--tree", action="store_true", help="Only generate the file tree."
    )
    parser.add_argument(
        "--code", action="store_true", help="Only generate the code summary."
    )

    args = parser.parse_args()

    if args.gui:
        input_directory = select_directory("Select the directory to analyze")
        output_directory = select_directory("Select the output directory")
    else:
        if not args.directory or not args.output_directory:
            parser.error("You must specify input and output directories or use --gui.")
        input_directory, output_directory = args.directory, args.output_directory

    if not args.tree and not args.code:
        args.tree, args.code = True, True  # Run both if no specific flag is set

    main(input_directory, output_directory, args.tree, args.code)
