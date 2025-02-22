import argparse
import json
import logging
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog

# Ensure src/ is in the Python module search path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from project_reader.code_summary import summarize_code
from project_reader.file_tree import generate_file_tree, get_project_name
from project_reader.markdown_output import save_as_markdown

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

    if not output_directory:
        output_directory = directory.parent

    ensure_directory_exists(output_directory)

    project_name = get_project_name(directory)

    file_tree_output = output_directory / f"{project_name}_file_tree.json"
    code_summary_output = output_directory / f"{project_name}_code_summary.json"
    gpt_summary_output = output_directory / f"{project_name}_gpt_summary.json"
    markdown_output = output_directory / f"{project_name}_summary.md"

    logging.info(f"Analyzing directory: {directory}")
    logging.info(f"Saving outputs to: {output_directory}")

    try:
        file_tree = generate_file_tree(directory)
        file_tree_output.write_text(json.dumps(file_tree, indent=4), encoding="utf-8")
        logging.info(f"File tree saved to {file_tree_output}")

        code_summaries, gpt_summaries = summarize_code(directory)
        code_summary_output.write_text(
            json.dumps(code_summaries, indent=4), encoding="utf-8"
        )
        gpt_summary_output.write_text(
            json.dumps(gpt_summaries, indent=4), encoding="utf-8"
        )
        logging.info(f"Code summary saved to {code_summary_output}")
        logging.info(f"GPT-friendly summary saved to {gpt_summary_output}")

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
    args = parser.parse_args()

    input_directory = select_directory("Select the directory to analyze")
    if not input_directory:
        logging.error("No input directory selected. Exiting.")
        exit(1)

    output_directory = select_directory(
        "Select the output directory (Cancel to use default)"
    )

    if not output_directory:
        output_directory = input_directory.parent

    main(input_directory, output_directory)
