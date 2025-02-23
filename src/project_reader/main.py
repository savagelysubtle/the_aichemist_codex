import argparse
import asyncio
import json
import logging
import tkinter as tk
from pathlib import Path
from tkinter import filedialog

from .code_summary import summarize_code
from .file_tree import FileTreeGenerator, get_project_name
from .markdown_output import save_as_markdown

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def save_json(output_file, data):
    """Save JSON output in sorted order."""
    sorted_data = json.dumps(data, indent=4, sort_keys=True)
    output_file.write_text(sorted_data, encoding="utf-8")


def select_directory(prompt: str) -> Path:
    """Open a file dialog to let the user select a directory."""
    root = tk.Tk()
    root.withdraw()
    folder_selected = filedialog.askdirectory(title=prompt)
    return Path(folder_selected) if folder_selected else None


def ensure_directory_exists(directory: Path):
    """Ensure the output directory exists."""
    if not directory.exists():
        logging.info(f"Creating output directory: {directory}")
        directory.mkdir(parents=True, exist_ok=True)


def main(directory: Path, output_directory: Path):
    """Runs file tree and code summary analysis with GPT-compatible summarization."""
    if not directory or not directory.exists():
        logging.error("No valid directory selected for analysis.")
        return

    ensure_directory_exists(output_directory)

    project_name = get_project_name(directory)

    file_tree_output = output_directory / f"{project_name}_file_tree.json"
    code_summary_output = output_directory / f"{project_name}_code_summary.json"
    gpt_summary_output = output_directory / f"{project_name}_gpt_summary.json"
    markdown_output = output_directory / f"{project_name}_summary.md"

    logging.info(f"Analyzing directory: {directory}")
    logging.info(f"Saving outputs to: {output_directory}")

    try:
        # Generate file tree
        tree_generator = FileTreeGenerator()
        file_tree = asyncio.run(tree_generator.generate(directory))
        file_tree_output.write_text(json.dumps(file_tree, indent=4), encoding="utf-8")
        logging.info(f"File tree saved to {file_tree_output}")

        # Run code summarization
        code_summaries, gpt_summaries = asyncio.run(summarize_code(directory))
        code_summary_output.write_text(
            json.dumps(code_summaries, indent=4), encoding="utf-8"
        )
        gpt_summary_output.write_text(
            json.dumps(gpt_summaries, indent=4), encoding="utf-8"
        )
        logging.info(f"Code summary saved to {code_summary_output}")
        logging.info(f"GPT-friendly summary saved to {gpt_summary_output}")

        # Save Markdown output
        save_as_markdown(
            markdown_output, code_summaries, gpt_summaries, "Project Code Summary"
        )
        logging.info(f"Markdown summary saved to {markdown_output}")

    except Exception as e:
        logging.error(f"An error occurred: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Analyze a directory for file structure and code summaries."
    )
    parser.add_argument("--dir", type=Path, help="Directory to analyze")
    parser.add_argument("--out", type=Path, help="Output directory (optional)")
    args = parser.parse_args()

    # Use CLI arguments if provided; otherwise, prompt the user
    input_directory = args.dir or select_directory("Select the directory to analyze")
    if not input_directory:
        logging.error("No input directory selected. Exiting.")
        exit(1)

    output_directory = args.out or select_directory(
        "Select the output directory (Cancel to use default)"
    )

    if not output_directory:
        output_directory = input_directory.parent

    main(input_directory, output_directory)
