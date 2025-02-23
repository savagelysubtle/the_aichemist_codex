import argparse
import ast
import asyncio
import json
import logging
from pathlib import Path

from common.async_io import AsyncFileReader

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


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

        return file_path.resolve().as_posix(), summaries

    except SyntaxError as e:
        logging.error(f"Syntax error in {file_path}: {e}")
        return file_path.resolve().as_posix(), {"error": f"Syntax error: {e}"}
    except Exception as e:
        logging.error(f"Error processing {file_path}: {e}")
        return file_path.resolve().as_posix(), {"error": str(e)}


async def summarize_code(directory: Path):
    """Analyzes Python code in a directory."""
    directory = Path(directory)
    python_files = list(directory.glob("**/*.py"))

    tasks = [process_file(file) for file in python_files]
    results = await asyncio.gather(*tasks)

    return {file: summary for file, summary in results}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Summarize Python code.")
    parser.add_argument("directory", type=Path, help="Directory to analyze.")
    args = parser.parse_args()

    logging.info(f"Starting code analysis for {args.directory}")
    summary = asyncio.run(summarize_code(args.directory))

    output_file = args.directory.parent / "code_summary.json"
    output_file.write_text(json.dumps(summary, indent=4), encoding="utf-8")
    logging.info(f"Code summary saved to {output_file}")
