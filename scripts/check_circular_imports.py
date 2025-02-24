"""Script to detect circular imports in the project."""

import ast
import logging
from collections import defaultdict
from pathlib import Path

logger = logging.getLogger(__name__)

# Define the base directory to scan
BASE_DIR = Path(__file__).resolve().parent

# List of Python files to check
python_files = list(BASE_DIR.rglob("*.py"))

# Store dependencies
dependencies = defaultdict(set)

# Extract imports from files
for file in python_files:
    with file.open("r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=str(file))

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                dependencies[file.name].add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            dependencies[file.name].add(node.module)

# Detect circular dependencies
for file, imports in dependencies.items():
    for imp in imports:
        if imp in dependencies and file in dependencies[imp]:
            logger.error(f"⚠️ Circular import detected: {file} <-> {imp}")
