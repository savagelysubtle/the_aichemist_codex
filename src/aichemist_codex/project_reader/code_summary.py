"""Analyzes Python code and generates structured summaries."""

import argparse
import ast
import asyncio
import json
import logging
from pathlib import Path

from aichemist_codex.output.json_writer import save_as_json
from aichemist_codex.output.markdown_writer import save_as_markdown
from aichemist_codex.utils.async_io import AsyncFileReader
from aichemist_codex.utils.safety import SafeFileHandler

logger = logging.getLogger(__name__)


def get_function_metadata(node):
    """Extracts function metadata including decorators and return types."""
    decorators = [d.id for d in node.decorator_list if isinstance(d, ast.Name)]
    return_type = ast.unparse(node.returns) if node.returns else None

    return {
        "name": node.name,
        "args": [arg.arg for arg in node.args.args],
        "decorators": decorators,
        "return_type": return_type,
        "lineno": node.lineno,
    }


async def process_file(file_path: Path):
    """Extracts function and class details from a Python file, including docstrings and line numbers."""
    try:
        code = await AsyncFileReader.read(file_path)
        tree = ast.parse(code, filename=str(file_path))

        file_summary = ast.get_docstring(tree) or "No summary available."
        summaries = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                docstring = ast.get_docstring(node) or "No docstring provided."
                summaries.append(
                    {
                        "name": node.name,
                        "args": [arg.arg for arg in node.args.args],
                        "lineno": node.lineno,
                        "docstring": docstring,
                    }
                )

        folder_name = file_path.parent.name  # Extracts the folder name

        return file_path.resolve().as_posix(), {
            "summary": file_summary,
            "folder": folder_name,
            "functions": summaries,
        }

    except SyntaxError as e:
        logging.error(f"Syntax error in {file_path}: {e}")
        return file_path.resolve().as_posix(), {
            "summary": "Syntax error.",
            "folder": file_path.parent.name,
            "functions": [],
        }
    except Exception as e:
        logging.error(f"Error processing {file_path}: {e}")
        return file_path.resolve().as_posix(), {
            "summary": "Processing error.",
            "folder": file_path.parent.name,
            "functions": [],
        }


async def summarize_code(directory: Path):
    """Analyzes Python code in a directory, skipping ignored files."""
    directory = directory.resolve()  # Ensure absolute path

    # ✅ Instead of using `rglob`, manually scan to filter out directories first
    python_files = []
    for path in directory.glob("**/*.py"):
        if SafeFileHandler.should_ignore(path):
            continue  # Skip ignored files and directories
        python_files.append(path)

    if not python_files:
        logger.warning(
            f"No Python files found in {directory} after filtering ignored paths."
        )

    tasks = [process_file(file) for file in python_files]
    results = await asyncio.gather(*tasks, return_exceptions=True)  # Handle errors

    valid_results = {}
    for res in results:
        if isinstance(res, tuple) and len(res) == 2:  # Ensure correct format
            valid_results[res[0]] = res[1]
        else:
            logging.error(f"Invalid result from process_file(): {res}")

    return valid_results


def summarize_project(directory: Path, output_markdown: Path, output_json: Path):
    """Runs the code summarization process and saves multiple output formats."""
    summary = asyncio.run(summarize_code(directory))

    # ✅ Debugging: Log output before saving
    logger.info(
        f"Summarization completed. Sample output: {json.dumps(list(summary.items())[:2], indent=4)}"
    )

    if not summary:
        logger.error("No files were analyzed. The summary is empty.")

    save_as_markdown(output_markdown, summary, {}, "Project Code Summary")
    save_as_json(output_json, summary)

    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Summarize Python code.")
    parser.add_argument("directory", type=Path, help="Directory to analyze.")
    args = parser.parse_args()

    input_directory = args.directory.resolve()  # Ensure absolute path
    logging.info(f"Starting code analysis for {input_directory}")

    output_json_file = input_directory / "code_summary.json"
    output_md_file = input_directory / "code_summary.md"

    summary = summarize_project(input_directory, output_md_file, output_json_file)

    logging.info(f"Code summary saved to {output_json_file}")
    logging.info(f"Markdown summary saved to {output_md_file}")
