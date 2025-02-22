import argparse
import ast
import concurrent.futures
import json
import logging
from pathlib import Path

from project_reader.file_tree import (
    get_project_name,
    list_python_files,
    summarize_for_gpt,
)

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def get_function_args(node):
    """Extract function arguments, including *args and **kwargs."""
    args = [arg.arg for arg in node.args.args]
    if node.args.vararg:
        args.append(f"*{node.args.vararg.arg}")
    if node.args.kwarg:
        args.append(f"**{node.args.kwarg.arg}")
    return args


def process_file(file_path: Path):
    """Extract function/class definitions and summarize them for GPT."""
    try:
        with file_path.open("r", encoding="utf-8") as f:
            code = f.read()
        tree = ast.parse(code)

        summaries = []
        raw_summary = []  # Stores extracted function/class descriptions

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                summary = {
                    "type": "function",
                    "name": node.name,
                    "args": get_function_args(node),
                    "lineno": node.lineno,
                }
                summaries.append(summary)
                raw_summary.append(f"Function `{node.name}` (line {node.lineno})")

            elif isinstance(node, ast.ClassDef):
                methods = [
                    f"Method `{method.name}` (line {method.lineno})"
                    for method in node.body
                    if isinstance(method, ast.FunctionDef)
                ]
                summary = {
                    "type": "class",
                    "name": node.name,
                    "methods": methods if methods else None,
                    "lineno": node.lineno,
                }
                summaries.append(summary)
                raw_summary.append(
                    f"Class `{node.name}` with {len(methods)} methods (line {node.lineno})"
                )

        # Generate GPT-friendly summary
        gpt_summary = summarize_for_gpt(". ".join(raw_summary))

        return file_path.resolve().as_posix(), summaries, gpt_summary

    except SyntaxError as e:
        logging.error(f"Syntax error in {file_path}: {e}")
        return file_path.resolve().as_posix(), {"error": f"Syntax error: {str(e)}"}, ""

    except Exception as e:
        logging.error(f"Error processing {file_path}: {e}")
        return file_path.resolve().as_posix(), {"error": str(e)}, ""


def summarize_code(directory: Path):
    """Parallelize code analysis and generate both full and GPT-friendly summaries."""
    directory = Path(directory)
    python_files = list_python_files(directory)

    if not python_files:
        logging.warning(f"No Python files found in '{directory}'.")
        return {}, {}

    code_summaries = {}
    gpt_summaries = {}

    with concurrent.futures.ProcessPoolExecutor() as executor:
        results = executor.map(process_file, python_files)

    for file_path, summary, gpt_summary in results:
        code_summaries[file_path] = summary
        gpt_summaries[file_path] = gpt_summary

    return code_summaries, gpt_summaries


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Summarize functions and classes in Python files."
    )
    parser.add_argument(
        "directory", type=Path, help="Directory to analyze for Python code."
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output JSON file for code summary. Defaults to <project_name>_code_summary.json",
    )

    args = parser.parse_args()
    project_name = get_project_name(args.directory)

    output_file = (
        args.output
        if args.output
        else args.directory.parent / f"{project_name}_code_summary.json"
    )

    logging.info(f"Starting code analysis for directory: {args.directory}")

    summary = summarize_code(args.directory)

    output_file.write_text(json.dumps(summary, indent=4), encoding="utf-8")

    logging.info(f"Code summary saved to {output_file}")
