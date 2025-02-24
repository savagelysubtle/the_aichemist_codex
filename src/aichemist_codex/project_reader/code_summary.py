"""Analyzes Python code and generates structured summaries."""

import argparse
import ast
import asyncio
import logging
from pathlib import Path

from aichemist_codex.output.json_writer import save_as_json
from aichemist_codex.output.markdown_writer import save_as_markdown
from aichemist_codex.utils.async_io import AsyncFileReader

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
    """Extracts function and class details from a Python file."""
    try:
        code = await AsyncFileReader.read(file_path)
        tree = ast.parse(code, filename=str(file_path))

        summaries = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                summaries.append(get_function_metadata(node))
            elif isinstance(node, ast.ClassDef):
                summaries.append(
                    {
                        "type": "class",
                        "name": node.name,
                        "methods": [
                            m.name for m in node.body if isinstance(m, ast.FunctionDef)
                        ],
                        "lineno": node.lineno,
                    }
                )

        return (str(file_path.resolve()), summaries)  # Ensure tuple with string path

    except SyntaxError as e:
        logging.error(f"Syntax error in {file_path}: {e}")
        return (str(file_path.resolve()), {"error": f"Syntax error: {e}"})
    except Exception as e:
        logging.error(f"Error processing {file_path}: {e}")
        return (str(file_path.resolve()), {"error": str(e)})  # Ensure tuple


async def summarize_code(directory: Path):
    """Analyzes Python code in a directory."""
    directory = directory.resolve()  # Ensure absolute path
    python_files = list(directory.glob("**/*.py"))

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

    # ✅ Now uses the new output module
    save_as_markdown(
        output_markdown, summary, {}, "Project Code Summary"
    )  # Empty GPT summaries for now
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
