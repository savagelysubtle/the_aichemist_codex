"""Analyzes Python code and generates structured summaries."""

import argparse
import ast
import asyncio
import json
import logging
from pathlib import Path

from the_aichemist_codex.infrastructure.utils.common.safety import SafeFileHandler

# Use the project's existing utilities instead of the problematic imports
from the_aichemist_codex.infrastructure.utils.io.async_io import AsyncFileIO

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
    """
    Extracts function and class details from a Python file.

    Args:
        file_path: Path to the file to process

    Returns:
        Tuple of (file_path, file_data)
    """
    try:
        # Read file contents using the project's AsyncFileIO utility
        code = await AsyncFileIO.read_text(file_path)

        # Check if reading the file encountered an error (AsyncFileIO returns error messages as strings)
        if code.startswith("# Error") or code.startswith("# Encoding"):
            logger.error(f"Error reading {file_path}: {code}")
            return file_path.resolve().as_posix(), {
                "summary": code,
                "folder": file_path.parent.name,
                "functions": [],
                "classes": [],
                "line_count": 0,
                "file_type": file_path.suffix,
            }

        # Parse the AST
        tree = ast.parse(code, filename=str(file_path))

        # Get the module docstring (summary)
        file_summary = ast.get_docstring(tree) or "No summary available."

        # Extract functions
        functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                docstring = ast.get_docstring(node) or "No docstring provided."
                functions.append(
                    {
                        "name": node.name,
                        "args": [arg.arg for arg in node.args.args],
                        "lineno": node.lineno,
                        "docstring": docstring,
                    }
                )

        # Extract classes
        classes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                docstring = ast.get_docstring(node) or "No docstring provided."
                class_info = {
                    "name": node.name,
                    "lineno": node.lineno,
                    "docstring": docstring,
                    "methods": [],
                    "properties": [],
                }

                # Get methods
                for child in ast.iter_child_nodes(node):
                    if isinstance(child, ast.FunctionDef):
                        method_docstring = (
                            ast.get_docstring(child) or "No docstring provided."
                        )
                        class_info["methods"].append(
                            {
                                "name": child.name,
                                "args": [arg.arg for arg in child.args.args],
                                "lineno": child.lineno,
                                "docstring": method_docstring,
                            }
                        )

                classes.append(class_info)

        # Create a summary of the file
        file_data = {
            "summary": file_summary,
            "folder": file_path.parent.name,
            "functions": functions,
            "classes": classes,
            "line_count": len(code.splitlines()),
            "file_type": file_path.suffix,
        }

        return file_path.resolve().as_posix(), file_data

    except SyntaxError as e:
        logger.error(f"Syntax error in {file_path}: {e}")
        return file_path.resolve().as_posix(), {
            "summary": f"Syntax error: {str(e)}",
            "folder": file_path.parent.name,
            "functions": [],
            "classes": [],
            "line_count": 0,
            "file_type": file_path.suffix,
        }
    except Exception as e:
        logger.error(f"Error processing {file_path}: {e}")
        return file_path.resolve().as_posix(), {
            "summary": f"Processing error: {str(e)}",
            "folder": file_path.parent.name,
            "functions": [],
            "classes": [],
            "line_count": 0,
            "file_type": file_path.suffix,
        }


async def summarize_code(directory: Path):
    """Analyzes Python code in a directory, skipping ignored files."""
    directory = directory.resolve()  # Ensure absolute path

    # Get Python files, skipping ignored ones using SafeFileHandler
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


async def summarize_project(directory: Path, output_markdown: Path, output_json: Path):
    """Runs the code summarization process and saves multiple output formats."""
    summary = await summarize_code(directory)

    # Log output before saving
    logger.info(
        f"Summarization completed. Sample output: {json.dumps(list(summary.items())[:2], indent=4)}"
    )

    if not summary:
        logger.error("No files were analyzed. The summary is empty.")
        return summary

    # Instead of using the unavailable save_as methods, use AsyncFileIO to save files
    json_str = json.dumps(summary, indent=2)
    await AsyncFileIO.write(output_json, json_str)

    # Create basic markdown output
    md_content = "# Project Code Summary\n\n"
    for file_path, file_data in summary.items():
        md_content += f"## {Path(file_path).name}\n\n"
        md_content += f"**Summary:** {file_data['summary']}\n\n"

        if file_data["functions"]:
            md_content += "### Functions\n\n"
            for func in file_data["functions"]:
                md_content += f"- `{func['name']}`: {func['docstring']}\n"
            md_content += "\n"

        if file_data["classes"]:
            md_content += "### Classes\n\n"
            for cls in file_data["classes"]:
                md_content += f"- `{cls['name']}`: {cls['docstring']}\n"
            md_content += "\n"

        md_content += "---\n\n"

    await AsyncFileIO.write(output_markdown, md_content)

    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Summarize Python code.")
    parser.add_argument("directory", type=Path, help="Directory to analyze.")
    args = parser.parse_args()

    input_directory = args.directory.resolve()  # Ensure absolute path
    logging.info(f"Starting code analysis for {input_directory}")

    output_json_file = input_directory / "code_summary.json"
    output_md_file = input_directory / "code_summary.md"

    summary = asyncio.run(
        summarize_project(input_directory, output_md_file, output_json_file)
    )

    logging.info(f"Code summary saved to {output_json_file}")
    logging.info(f"Markdown summary saved to {output_md_file}")
