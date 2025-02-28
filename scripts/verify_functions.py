"""Script to verify that all function calls are defined somewhere in the project."""

import ast
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Define the base directory to scan
BASE_DIR = Path(__file__).resolve().parent

# List of Python files to check
python_files = list(BASE_DIR.rglob("*.py"))


# Function to extract function names from a file
def extract_functions(file_path: Path):
    """Parses a Python file and extracts all function definitions."""
    with file_path.open("r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=str(file_path))

    return {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}


# Function to extract function calls from a file
def extract_function_calls(file_path: Path):
    """Parses a Python file and extracts all function calls."""
    with file_path.open("r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=str(file_path))

    return {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }


# Build a global function reference
defined_functions = set()
for file in python_files:
    defined_functions.update(extract_functions(file))

# Check function calls
for file in python_files:
    called_functions = extract_function_calls(file)
    for func in called_functions:
        if func not in defined_functions:
            logger.error(
                f"⚠️  Function '{func}()' is called in {file} but not defined anywhere."
            )
