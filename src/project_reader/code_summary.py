import argparse
import ast
import asyncio
import json
import logging
from pathlib import Path

from project_reader.file_tree import list_python_files
from common.async_io import AsyncFileReader
from common.utils import get_project_name

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def get_function_args(node):
    """
    Extracts function arguments, including *args and **kwargs.
    """
    args = [arg.arg for arg in node.args.args]
    if node.args.vararg:
        args.append(f"*{node.args.vararg.arg}")
    if node.args.kwarg:
        args.append(f"**{node.args.kwarg.arg}")
    return args


async def process_file(file_path: Path):
    """
    Asynchronously extracts function and class definitions from a Python file.
    """
    try:
        code = await AsyncFileReader.read(file_path)
        tree = ast.parse(code, filename=str(file_path))
        summaries = []
        raw_summary = []

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

        return file_path.resolve().as_posix(), summaries, " ".join(raw_summary)

    except SyntaxError as e:
        logging.error(f"Syntax error in {file_path}: {e}")
        return file_path.resolve().as_posix(), {"error": f"Syntax error: {str(e)}"}, ""
    except Exception as e:
        logging.error(f"Error processing {file_path}: {e}")
        return file_path.resolve().as_posix(), {"error": str(e)}, ""


async def summarize_code(directory: Path):
    """
    Asynchronously analyzes Python code in a directory.
    """
    directory = Path(directory)
    python_files = list_python_files(directory)
    if not python_files:
        logging.warning(f"No Python files found in '{directory}'.")
        return {}, {}

    tasks = [process_file(file) for file in python_files]
    results = await asyncio.gather(*tasks)

    code_summaries = {file: summary for file, summary, _ in results}
    gpt_summaries = {file: gpt_summary for file, _, gpt_summary in results}

    return code_summaries, gpt_summaries


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Summarize Python code in a directory."
    )
    parser.add_argument("directory", type=Path, help="Directory to analyze.")
    parser.add_argument(
        "-o", "--output", type=Path, help="Output JSON file for code summary."
    )
    args = parser.parse_args()

    project_name = get_project_name(args.directory)
    output_file = (
        args.output
        if args.output
        else args.directory.parent / f"{project_name}_code_summary.json"
    )

    logging.info(f"Starting code analysis for {args.directory}")
    summary = asyncio.run(summarize_code(args.directory))

    output_file.write_text(json.dumps(summary, indent=4), encoding="utf-8")
    logging.info(f"Code summary saved to {output_file}")
