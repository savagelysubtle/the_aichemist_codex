#!/usr/bin/env python
"""
Script to fix circular import issues in the file_manager package.

This script analyzes the imports in the file_manager package and suggests
changes to fix circular dependencies.
"""

import os
import re
import sys
from pathlib import Path


def analyze_imports(file_path):
    """Analyze imports in the given file."""
    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    # Find all import statements
    import_pattern = r"(?:from\s+([.\w]+)\s+import\s+([^#\n]+)|import\s+([^#\n]+))"
    imports = re.findall(import_pattern, content)

    # Process imports
    result = []
    for from_module, from_imports, direct_imports in imports:
        if from_module:
            # Handle 'from X import Y' statements
            imports_list = [imp.strip() for imp in from_imports.split(",")]
            for imp in imports_list:
                result.append((from_module, imp))
        else:
            # Handle 'import X' statements
            imports_list = [imp.strip() for imp in direct_imports.split(",")]
            for imp in imports_list:
                result.append((imp, None))

    return result


def find_circular_imports(base_dir):
    """Find circular imports in the given directory."""
    # Get all Python files in the directory
    py_files = []
    for root, _, files in os.walk(base_dir):
        for file in files:
            if file.endswith(".py"):
                py_files.append(os.path.join(root, file))

    # Analyze imports in each file
    file_imports = {}
    for file_path in py_files:
        rel_path = os.path.relpath(file_path, base_dir)
        module_name = os.path.splitext(rel_path)[0].replace(os.path.sep, ".")
        file_imports[module_name] = analyze_imports(file_path)

    # Find circular dependencies
    circular_deps = []
    for module, imports in file_imports.items():
        for from_module, from_import in imports:
            if from_module in file_imports:
                # Check if the imported module imports back
                for back_from, back_import in file_imports[from_module]:
                    if back_from == module:
                        circular_deps.append(
                            (module, from_module, from_import, back_import)
                        )

    return circular_deps, file_imports


def suggest_fixes(circular_deps, file_imports):
    """Suggest fixes for circular dependencies."""
    suggestions = []

    for module, from_module, from_import, back_import in circular_deps:
        # Determine which import is more critical
        module_short = module.split(".")[-1]
        from_module_short = from_module.split(".")[-1]

        suggestion = f"Circular dependency between {module} and {from_module}:\n"
        suggestion += f"  - {module} imports {from_import} from {from_module}\n"
        suggestion += f"  - {from_module} imports {back_import} from {module}\n\n"

        suggestion += "Suggested fixes:\n"
        suggestion += f"1. Move shared functionality to a new module (e.g., '{module_short}_{from_module_short}_common.py')\n"
        suggestion += f"2. Use lazy imports in {module} or {from_module}:\n"
        suggestion += "   ```python\n"
        suggestion += "   def some_function():\n"
        suggestion += f"       from {from_module} import {from_import}  # Import inside function\n"
        suggestion += "       # Use the imported module\n"
        suggestion += "   ```\n"
        suggestion += "3. Use type hints with quotes for forward references:\n"
        suggestion += "   ```python\n"
        suggestion += (
            f"   def process_item(item: '{from_module_short}.{from_import}') -> None:\n"
        )
        suggestion += "       # Process the item\n"
        suggestion += "   ```\n"

        suggestions.append(suggestion)

    return suggestions


def main():
    """Main entry point."""
    # Get the base directory
    base_dir = Path(__file__).parent

    print(f"Analyzing imports in {base_dir}...")

    # Find circular imports
    circular_deps, file_imports = find_circular_imports(base_dir)

    if not circular_deps:
        print("No circular dependencies found!")
        return 0

    print(f"Found {len(circular_deps)} circular dependencies:")
    for module, from_module, from_import, back_import in circular_deps:
        print(f"  - {module} <-> {from_module}")

    print("\nSuggested fixes:")
    suggestions = suggest_fixes(circular_deps, file_imports)
    for i, suggestion in enumerate(suggestions, 1):
        print(f"\nSuggestion {i}:")
        print(suggestion)

    return 0


if __name__ == "__main__":
    sys.exit(main())
