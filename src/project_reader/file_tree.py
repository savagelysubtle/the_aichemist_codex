import argparse
import json
import logging
from pathlib import Path
import ast

from project_reader.logging_config import setup_logging
from common.utils import get_project_name

setup_logging()

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ✅ Exclude directories to avoid unnecessary processing
EXCLUDED_DIRS = {".venv", "venv", "myenv", "Lib", "site-packages", "__pycache__", "node_modules", "dist", "build"}
MAX_DEPTH = 10  # ✅ Prevent infinite recursion

def generate_file_tree(directory: Path, depth=0) -> dict:
    """Recursively generates a file tree dictionary structure while handling errors."""
    if depth > MAX_DEPTH:
        return {"ERROR": "Max depth reached"}  # ✅ Prevent infinite loops

    tree = {}

    try:
        for entry in sorted(directory.iterdir(), key=lambda e: e.name.lower()):
            if any(excluded in entry.parts for excluded in EXCLUDED_DIRS):
                continue  # ✅ Skip unnecessary directories

            if entry.is_dir():
                tree[entry.name] = generate_file_tree(entry, depth + 1)
            else:
                tree[entry.name] = None  # Files are leaf nodes

    except PermissionError:
        logging.error(f"Permission denied: {directory}")
        tree["ERROR"] = "Permission denied"

    except Exception as e:
        logging.error(f"Unexpected error while reading {directory}: {e}")
        tree["ERROR"] = str(e)

    return tree

def safe_read_file(file_path):
    """Reads a file safely, handling encoding errors and large files."""
    MAX_FILE_SIZE_MB = 10  # ✅ Skip files larger than 10MB

    if file_path.stat().st_size > MAX_FILE_SIZE_MB * 1024 * 1024:
        logging.warning(f"Skipping large file: {file_path}")
        return None  # ✅ Skip large files

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception as e:
        logging.error(f"Skipping file {file_path}: {e}")
        return None  # ✅ Skip file if unreadable

def parse_python_code(file_path):
    """Parses Python code and extracts functions/classes while avoiding syntax errors."""
    content = safe_read_file(file_path)
    if content is None:
        return []  # ✅ Skip if unreadable

    try:
        tree = ast.parse(content, filename=str(file_path))
        return [node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.ClassDef))]
    except SyntaxError as e:
        logging.warning(f"Skipping {file_path} due to syntax error: {e}")
        return []  # ✅ Skip files with syntax errors

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a file tree for a given directory.")
    parser.add_argument("directory", type=Path, help="Path to the directory to analyze.")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output JSON file for file tree. Defaults to <project_name>_file_tree.json",
    )

    args = parser.parse_args()
    project_name = get_project_name(args.directory)

    # Determine output file name
    output_file = args.output if args.output else args.directory.parent / f"{project_name}_file_tree.json"

    logging.info(f"Generating file tree for {args.directory}")
    file_tree = generate_file_tree(args.directory)

    output_file.write_text(json.dumps(file_tree, indent=4), encoding="utf-8")

    logging.info(f"File tree saved to {output_file}")
