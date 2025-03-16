#!/usr/bin/env python
"""
API Documentation Generator for The Aichemist Codex.

This script automatically generates API documentation for the project
by scanning the codebase and creating RST files for Sphinx.
"""

import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def main() -> None:
    """Generate API documentation for The Aichemist Codex."""
    print("Generating API documentation...")

    # Configuration for modules to document
    api_dir = Path(__file__).resolve().parent / "api"
    src_dir = Path(__file__).resolve().parent.parent / "backend" / "src"

    # Ensure the API directory exists
    api_dir.mkdir(exist_ok=True)

    # Define the modules to document
    # Format: module_name -> [submodule1, submodule2, ...]
    modules: dict[str, list[str]] = {
        "file_reader": [],
        "file_manager": ["directory_monitor", "directory_organizer", "change_detector"],
        "metadata": ["extractors", "analyzers"],
        "search": ["engines", "indexers", "query_parser"],
        "relationships": ["detector", "graph", "detectors"],
        "rollback": ["transaction", "snapshot"],
        "security": ["permissions", "encryption", "authentication"],
        "ai": ["embeddings", "clustering", "recommendation"],
        "integration": ["plugins", "api", "exporters"],
        "ui": ["cli", "components", "dashboards"],
        "utils": ["validators", "profilers", "helpers"],
        "config": ["settings", "validation", "secure_config"],
    }

    # Generate API documentation for all modules
    generate_api_docs(modules, api_dir, src_dir)

    # Create an index for the API documentation
    create_api_index(modules, api_dir)

    print("✅ API documentation generated successfully!")


def get_module_description(module_name: str) -> str:
    """
    Get a description of a module based on its name.

    Args:
        module_name: The name of the module

    Returns:
        str: A description of the module
    """
    descriptions = {
        "file_reader": "reading and processing different file types",
        "file_manager": "managing file operations and organization",
        "metadata": "extracting and analyzing file metadata",
        "search": "searching for files and content",
        "relationships": "mapping relationships between files",
        "rollback": "providing transaction-based undo capabilities",
        "security": "ensuring secure file operations",
        "ai": "providing AI-powered features",
        "integration": "integrating with external systems",
        "ui": "providing user interface components",
        "utils": "providing utility functions",
        "config": "configuration management",
    }

    return descriptions.get(module_name, "providing functionality for the project")


def generate_api_docs(
    modules: dict[str, list[str]], api_dir: Path, src_dir: Path
) -> None:
    """
    Generate RST files for each module.

    Args:
        modules: Dictionary mapping module names to lists of submodules
        api_dir: Directory to store the generated RST files
        src_dir: Directory containing the source code
    """
    # Generate documentation for each module
    for module_name, submodules in modules.items():
        title = f"{module_name.replace('_', ' ').title()} Module"

        # Create module documentation
        module_path = src_dir / module_name
        # Check if init exists but don't assign to variable since we're not using it
        (module_path / "__init__.py").exists()

        with open(api_dir / f"{module_name}.rst", "w") as f:
            f.write(
                "\n".join(
                    [
                        title,
                        "=" * len(title),
                        "",
                        # Break long line into multiple lines to avoid linting issue
                        f"The {title} module provides functionality for ",
                        f"{get_module_description(module_name)}.",
                        "",
                        f".. automodule:: backend.src.{module_name}",
                        "   :members:",
                        "   :undoc-members:",
                        "   :show-inheritance:",
                        "",
                    ]
                )
            )

        # Process submodules if they exist
        if submodules:
            # Create submodule directory
            (api_dir / module_name).mkdir(exist_ok=True)

            # Create submodule index
            with open(api_dir / module_name / "index.rst", "w") as f:
                f.write(
                    "\n".join(
                        [
                            f"{title} API",
                            "=" * len(f"{title} API"),
                            "",
                            ".. toctree::",
                            "   :maxdepth: 2",
                            "",
                        ]
                        + [f"   {submodule}" for submodule in submodules]
                    )
                )

            # Create documentation for each submodule
            for submodule in submodules:
                submodule_path = module_path / f"{submodule}.py"
                if not submodule_path.exists():
                    submodule_path = module_path / submodule

                if submodule_path.exists():
                    with open(api_dir / module_name / f"{submodule}.rst", "w") as f:
                        sub_title = f"{submodule.replace('_', ' ').title()}"
                        f.write(
                            "\n".join(
                                [
                                    sub_title,
                                    "=" * len(sub_title),
                                    "",
                                    f".. automodule:: backend.src.{module_name}.{submodule}",
                                    "   :members:",
                                    "   :undoc-members:",
                                    "   :show-inheritance:",
                                    "",
                                ]
                            )
                        )


def create_api_index(modules: dict[str, list[str]], api_dir: Path) -> None:
    """
    Create an index file for the API documentation.

    Args:
        modules: Dictionary mapping module names to lists of submodules
        api_dir: Directory to store the generated RST files
    """
    with open(api_dir / "index.rst", "w") as f:
        f.write(
            "\n".join(
                [
                    "API Reference",
                    "============",
                    "",
                    ".. toctree::",
                    "   :maxdepth: 2",
                    "",
                ]
                + [f"   {module}" for module in sorted(modules.keys())]
            )
        )


if __name__ == "__main__":
    main()
