import argparse
import ast
import json
import logging
from pathlib import Path

from project_reader.logging_config import setup_logging

setup_logging()

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

EXCLUDED_DIRS = {
    ".venv",
    "venv",
    "myenv",
    "Lib",
    "site-packages",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
}
MAX_DEPTH = 10


def get_project_name(directory: Path) -> str:
    """Returns the project name based on the directory structure."""
    return directory.name


def generate_file_tree(directory: Path, depth=0) -> dict:
    """Recursively generates a file tree dictionary structure while handling errors."""
    if depth > MAX_DEPTH:
        return {"ERROR": "Max depth reached"}

    tree = {}

    try:
        for entry in sorted(directory.iterdir(), key=lambda e: e.name.lower()):
            if entry.name in EXCLUDED_DIRS:
                continue

            if entry.is_dir():
                tree[entry.name] = generate_file_tree(entry, depth + 1)
            else:
                tree[entry.name] = None
    except PermissionError:
        logging.error(f"Permission denied: {directory}")
        tree["ERROR"] = "Permission denied"
    except Exception as e:
        logging.error(f"Unexpected error while reading {directory}: {e}")
        tree["ERROR"] = str(e)

    return tree


def safe_read_file(file_path: Path) -> str:
    """Reads a file safely, handling encoding errors and large files."""
    MAX_FILE_SIZE_MB = 10

    if file_path.stat().st_size > MAX_FILE_SIZE_MB * 1024 * 1024:
        logging.warning(f"Skipping large file: {file_path}")
        return ""

    try:
        return file_path.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        logging.error(f"Skipping file {file_path}: {e}")
        return ""


def parse_python_code(file_path: Path) -> list:
    """Parses Python code and extracts function and class names while avoiding syntax errors."""
    content = safe_read_file(file_path)
    if not content:
        return []

    try:
        tree = ast.parse(content, filename=str(file_path))
        return [
            node.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.ClassDef))
        ]
    except SyntaxError as e:
        logging.warning(f"Skipping {file_path} due to syntax error: {e}")
        return []


def list_python_files(directory: Path) -> list:
    """Returns a list of Python files in a given directory."""
    return [file for file in directory.glob("**/*.py") if file.is_file()]


def summarize_for_gpt(file_tree_path: Path, gpt_summary_path: Path) -> str:
    """Generates a concise summary for GPT from the file tree."""
    if not file_tree_path.exists() or not gpt_summary_path.exists():
        logging.error("File tree or GPT summary file is missing.")
        return ""

    try:
        file_tree = json.loads(file_tree_path.read_text(encoding="utf-8"))
        gpt_summary = json.loads(gpt_summary_path.read_text(encoding="utf-8"))
    except Exception as e:
        logging.error(f"Error loading files: {e}")
        return ""

    summary = {}

    def summarize_tree(tree, path=""):
        for key, value in tree.items():
            full_path = f"{path}/{key}" if path else key
            if isinstance(value, dict):
                summarize_tree(value, full_path)
            elif full_path in gpt_summary:
                summary[full_path] = gpt_summary[full_path]

    summarize_tree(file_tree)

    return json.dumps(summary, indent=4)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate a file tree for a given directory."
    )
    parser.add_argument(
        "directory", type=Path, help="Path to the directory to analyze."
    )
    parser.add_argument(
        "-o", "--output", type=Path, help="Output JSON file for file tree."
    )

    args = parser.parse_args()
    project_name = get_project_name(args.directory)
    output_file = (
        args.output or args.directory.parent / f"{project_name}_file_tree.json"
    )

    logging.info(f"Generating file tree for {args.directory}")
    file_tree = generate_file_tree(args.directory)

    output_file.write_text(json.dumps(file_tree, indent=4), encoding="utf-8")
    logging.info(f"File tree saved to {output_file}")
