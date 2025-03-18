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
    src_dir = Path(__file__).resolve().parent.parent / "src" / "the_aichemist_codex"
    backend_dir = src_dir / "backend"

    # Ensure the API directory exists
    api_dir.mkdir(exist_ok=True)

    # Define the modules to document
    # Format: module_name -> [submodule1, submodule2, ...]
    modules: dict[str, list[str]] = {
        "core": ["interfaces", "models", "constants", "exceptions", "utils"],
        "domain": [
            "analytics",
            "content_analyzer",
            "file_manager",
            "file_reader",
            "file_writer",
            "ingest",
            "metadata",
            "notification",
            "output_formatter",
            "project_reader",
            "relationships",
            "rollback",
            "search",
            "tagging",
            "user_management",
        ],
        "infrastructure": ["config", "file", "io", "paths"],
        "services": ["cache", "file", "metadata"],
        "api": ["cli", "rest", "external"],
        "tools": [],
        "registry": [],
    }

    # Generate API documentation for all modules
    generate_api_docs(modules, api_dir, backend_dir)

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
        "core": "core abstractions, interfaces, models, and utilities",
        "domain": "domain-specific business logic implementations",
        "infrastructure": "infrastructure and external service implementations",
        "services": "service implementations for the application",
        "api": "API interfaces for CLI, REST, and external interactions",
        "tools": "utility tools for the application",
        "registry": "dependency injection and service registry",
        # Domain submodules
        "analytics": "tracking and analyzing usage patterns",
        "content_analyzer": "analyzing and extracting information from content",
        "file_manager": "managing file operations and organization",
        "file_reader": "reading and processing different file types",
        "file_writer": "writing data to different file formats",
        "ingest": "ingesting content from various sources",
        "metadata": "extracting and managing file metadata",
        "notification": "managing notifications to users",
        "output_formatter": "formatting output in different formats",
        "project_reader": "reading and analyzing project structures",
        "relationships": "managing relationships between entities",
        "rollback": "providing undo and version control capabilities",
        "search": "searching and indexing content",
        "tagging": "managing tags and classifications",
        "user_management": "managing users, authentication, and authorization",
    }

    return descriptions.get(module_name, "providing functionality for the project")


def generate_api_docs(
    modules: dict[str, list[str]], api_dir: Path, backend_dir: Path
) -> None:
    """
    Generate RST files for each module.

    Args:
        modules: Dictionary mapping module names to lists of submodules
        api_dir: Directory to store the generated RST files
        backend_dir: Directory containing the backend source code
    """
    # Generate documentation for each module
    for module_name, submodules in modules.items():
        title = f"{module_name.replace('_', ' ').title()} Module"
        underline = "=" * len(title)
        module_path = f"the_aichemist_codex.backend.{module_name}"

        if module_name == "domain":
            # Special handling for domain module with more complex structure
            domain_dir = api_dir / "domain"
            domain_dir.mkdir(exist_ok=True)

            # Create a domain index file
            with open(api_dir / f"{module_name}.rst", "w") as f:
                f.write(f"{title}\n{underline}\n\n")
                f.write(f"The {title} provides functionality for ")
                f.write(f"{get_module_description(module_name)}.\n\n")
                f.write(".. toctree::\n   :maxdepth: 2\n\n")

                for submodule in submodules:
                    f.write(f"   domain/{submodule}\n")

                f.write("\n")
                f.write(f".. automodule:: {module_path}\n")
                f.write("   :members:\n")
                f.write("   :undoc-members:\n")
                f.write("   :show-inheritance:\n")
                f.write("   :imported-members:\n")

            # Create RST files for each domain submodule
            for submodule in submodules:
                submodule_title = f"{submodule.replace('_', ' ').title()} Module"
                submodule_underline = "=" * len(submodule_title)
                submodule_path = f"the_aichemist_codex.backend.domain.{submodule}"

                # Check if this domain submodule has its own submodules
                submodule_dir = backend_dir / "domain" / submodule
                subsub_dir = domain_dir / submodule

                if submodule_dir.is_dir() and any(submodule_dir.glob("*/")):
                    # Create a directory for this submodule's submodules
                    subsub_dir.mkdir(exist_ok=True)

                    # Create an index file for this submodule
                    with open(domain_dir / f"{submodule}.rst", "w") as f:
                        f.write(f"{submodule_title}\n{submodule_underline}\n\n")
                        f.write(f"The {submodule_title} provides functionality for ")
                        f.write(f"{get_module_description(submodule)}.\n\n")
                        f.write(".. toctree::\n   :maxdepth: 2\n\n")

                        # Find all Python modules in the submodule directory
                        for py_file in sorted(submodule_dir.glob("*.py")):
                            if (
                                py_file.name != "__init__.py"
                                and not py_file.name.startswith("_")
                            ):
                                subsub_name = py_file.stem
                                f.write(f"   {submodule}/{subsub_name}\n")

                        # Find all subdirectories with __init__.py
                        for subsub_dir in sorted(submodule_dir.glob("*/")):
                            if (subsub_dir / "__init__.py").exists():
                                subsub_name = subsub_dir.name
                                f.write(f"   {submodule}/{subsub_name}/index\n")

                        f.write("\n")
                        f.write(f".. automodule:: {submodule_path}\n")
                        f.write("   :members:\n")
                        f.write("   :undoc-members:\n")
                        f.write("   :show-inheritance:\n")
                        f.write("   :imported-members:\n")

                    # Create RST files for each Python module in the submodule directory
                    for py_file in sorted(submodule_dir.glob("*.py")):
                        if (
                            py_file.name != "__init__.py"
                            and not py_file.name.startswith("_")
                        ):
                            subsub_name = py_file.stem
                            subsub_title = f"{subsub_name.replace('_', ' ').title()}"
                            subsub_underline = "=" * len(subsub_title)
                            subsub_path = f"{submodule_path}.{subsub_name}"

                            with open(subsub_dir / f"{subsub_name}.rst", "w") as f:
                                f.write(f"{subsub_title}\n{subsub_underline}\n\n")
                                f.write(f".. automodule:: {subsub_path}\n")
                                f.write("   :members:\n")
                                f.write("   :undoc-members:\n")
                                f.write("   :show-inheritance:\n")
                                f.write("   :imported-members:\n")

                    # Create index.rst files for subdirectories with __init__.py
                    for subsub_dir_path in sorted(submodule_dir.glob("*/")):
                        if (subsub_dir_path / "__init__.py").exists():
                            subsub_dir_name = subsub_dir_path.name
                            subsub_dir_out = subsub_dir / subsub_dir_name
                            subsub_dir_out.mkdir(exist_ok=True)

                            subsub_dir_title = (
                                f"{subsub_dir_name.replace('_', ' ').title()} Module"
                            )
                            subsub_dir_underline = "=" * len(subsub_dir_title)
                            subsub_dir_path_mod = f"{submodule_path}.{subsub_dir_name}"

                            with open(subsub_dir_out / "index.rst", "w") as f:
                                f.write(
                                    f"{subsub_dir_title}\n{subsub_dir_underline}\n\n"
                                )
                                f.write(".. toctree::\n   :maxdepth: 2\n\n")

                                # Find all Python modules in the subdirectory
                                for py_file in sorted(subsub_dir_path.glob("*.py")):
                                    if (
                                        py_file.name != "__init__.py"
                                        and not py_file.name.startswith("_")
                                    ):
                                        subsubsub_name = py_file.stem
                                        f.write(f"   {subsubsub_name}\n")

                                f.write("\n")
                                f.write(f".. automodule:: {subsub_dir_path_mod}\n")
                                f.write("   :members:\n")
                                f.write("   :undoc-members:\n")
                                f.write("   :show-inheritance:\n")
                                f.write("   :imported-members:\n")

                            # Create RST files for each Python module in the subdirectory
                            for py_file in sorted(subsub_dir_path.glob("*.py")):
                                if (
                                    py_file.name != "__init__.py"
                                    and not py_file.name.startswith("_")
                                ):
                                    subsubsub_name = py_file.stem
                                    subsubsub_title = (
                                        f"{subsubsub_name.replace('_', ' ').title()}"
                                    )
                                    subsubsub_underline = "=" * len(subsubsub_title)
                                    subsubsub_path = (
                                        f"{subsub_dir_path_mod}.{subsubsub_name}"
                                    )

                                    with open(
                                        subsub_dir_out / f"{subsubsub_name}.rst", "w"
                                    ) as f:
                                        f.write(
                                            f"{subsubsub_title}\n{subsubsub_underline}\n\n"
                                        )
                                        f.write(f".. automodule:: {subsubsub_path}\n")
                                        f.write("   :members:\n")
                                        f.write("   :undoc-members:\n")
                                        f.write("   :show-inheritance:\n")
                                        f.write("   :imported-members:\n")
                else:
                    # Create a simple RST file for this submodule
                    with open(domain_dir / f"{submodule}.rst", "w") as f:
                        f.write(f"{submodule_title}\n{submodule_underline}\n\n")
                        f.write(f"The {submodule_title} provides functionality for ")
                        f.write(f"{get_module_description(submodule)}.\n\n")
                        f.write(f".. automodule:: {submodule_path}\n")
                        f.write("   :members:\n")
                        f.write("   :undoc-members:\n")
                        f.write("   :show-inheritance:\n")
                        f.write("   :imported-members:\n")
        else:
            # Standard module handling
            module_dir = backend_dir / module_name
            warning = ""

            if not module_dir.exists() or not module_dir.is_dir():
                warning = f"\n\n.. warning::\n   This module documentation might be incomplete because the module directory '{module_name}' was not found.\n"

            # Create an RST file for this module
            with open(api_dir / f"{module_name}.rst", "w") as f:
                f.write(f"{title}\n{underline}\n\n")
                f.write(f"The {title} provides functionality for ")
                f.write(f"{get_module_description(module_name)}.\n")
                f.write(warning)
                f.write("\n")
                f.write(f".. automodule:: {module_path}\n")
                f.write("   :members:\n")
                f.write("   :undoc-members:\n")
                f.write("   :show-inheritance:\n")
                f.write("   :imported-members:\n")

            # Handle submodules if any
            if submodules and module_dir.exists() and module_dir.is_dir():
                submodule_dir = api_dir / module_name
                submodule_dir.mkdir(exist_ok=True)

                # Create an index file for the submodules
                with open(submodule_dir / "index.rst", "w") as f:
                    f.write(f"{title} API\n{underline}\n\n")
                    f.write(".. toctree::\n   :maxdepth: 2\n\n")

                    for submodule in submodules:
                        f.write(f"   {submodule}\n")

                # Create RST files for each submodule
                for submodule in submodules:
                    submodule_title = f"{submodule.replace('_', ' ').title()}"
                    submodule_underline = "=" * len(submodule_title)
                    submodule_path = f"{module_path}.{submodule}"

                    with open(submodule_dir / f"{submodule}.rst", "w") as f:
                        f.write(f"{submodule_title}\n{submodule_underline}\n\n")
                        f.write(f".. automodule:: {submodule_path}\n")
                        f.write("   :members:\n")
                        f.write("   :undoc-members:\n")
                        f.write("   :show-inheritance:\n")
                        f.write("   :imported-members:\n")


def create_api_index(modules: dict[str, list[str]], api_dir: Path) -> None:
    """
    Create an index.rst file for the API documentation.

    Args:
        modules: Dictionary mapping module names to lists of submodules
        api_dir: Directory to store the generated RST files
    """
    with open(api_dir / "index.rst", "w") as f:
        f.write("API Reference\n============\n\n")
        f.write(".. toctree::\n   :maxdepth: 2\n\n")

        for module_name in modules:
            f.write(f"   {module_name}\n")


if __name__ == "__main__":
    main()
