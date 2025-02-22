import argparse
import json
import logging
from pathlib import Path

from project_reader.logging_config import setup_logging

from .config import CodexConfig
from .patterns import should_ignore

# Initialize logging and load config
setup_logging()
config = CodexConfig()  # Future use for modularizing per package

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

MAX_DEPTH = 10


def get_project_name(directory: Path) -> str:
    """Returns the project name based on the directory name."""
    return directory.name


def _is_safe_symlink(symlink: Path, base_dir: Path) -> bool:
    """
    Determines if a symlink resolves to a location within the base directory.
    """
    try:
        resolved = symlink.resolve(strict=True)
        return base_dir in resolved.parents or resolved == base_dir
    except Exception:
        return False


async def generate_file_tree(directory: Path, depth=0) -> dict:
    """
    Asynchronously generates a file tree dictionary structure.
    Applies pattern exclusion and checks symlink safety.
    """
    if depth > MAX_DEPTH:
        return {"error": "max_depth_exceeded"}

    tree = {}
    try:
        for entry in sorted(directory.iterdir(), key=lambda e: e.name.lower()):
            rel_path = str(entry.relative_to(directory))
            if should_ignore(rel_path):
                continue
            if entry.is_symlink() and not _is_safe_symlink(entry, directory):
                continue
            if entry.is_dir():
                tree[entry.name] = await generate_file_tree(entry, depth + 1)
            else:
                tree[entry.name] = None
    except PermissionError:
        logging.error(f"Permission denied: {directory}")
        tree["error"] = "permission_denied"
    except Exception as e:
        logging.error(f"Unexpected error while reading {directory}: {e}")
        tree["error"] = str(e)
    return tree


def safe_read_file(file_path: Path) -> str:
    """
    Reads a file safely, handling encoding issues and large file warnings.
    """
    MAX_FILE_SIZE_MB = 10
    if file_path.stat().st_size > MAX_FILE_SIZE_MB * 1024 * 1024:
        logging.warning(f"Skipping large file: {file_path}")
        return ""
    try:
        return file_path.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        logging.error(f"Error reading file {file_path}: {e}")
        return ""


def parse_python_code(file_path: Path) -> list:
    """
    Parses Python code to extract function and class names.
    """
    content = safe_read_file(file_path)
    if not content:
        return []
    try:
        import ast

        tree = ast.parse(content, filename=str(file_path))
        return [
            node.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.ClassDef))
        ]
    except SyntaxError as e:
        logging.warning(f"Syntax error in {file_path}: {e}")
        return []


def list_python_files(directory: Path) -> list:
    """
    Returns a list of Python files in the given directory and its subdirectories.
    """
    return [file for file in directory.glob("**/*.py") if file.is_file()]


def summarize_for_gpt(file_tree_path: Path, gpt_summary_path: Path) -> str:
    """
    Generates a concise summary for GPT based on the file tree and a GPT summary JSON.
    """
    if not file_tree_path.exists() or not gpt_summary_path.exists():
        logging.error("File tree or GPT summary file is missing.")
        return ""
    try:
        file_tree = json.loads(file_tree_path.read_text(encoding="utf-8"))
        gpt_summary = json.loads(gpt_summary_path.read_text(encoding="utf-8"))
    except Exception as e:
        logging.error(f"Error loading JSON files: {e}")
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
        args.output
        if args.output
        else args.directory.parent / f"{project_name}_file_tree.json"
    )

    import asyncio

    logging.info(f"Generating file tree for {args.directory}")
    tree = asyncio.run(generate_file_tree(args.directory))
    output_file.write_text(json.dumps(tree, indent=4), encoding="utf-8")
    logging.info(f"File tree saved to {output_file}")
