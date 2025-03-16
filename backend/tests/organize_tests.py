"""
Script to organize test files into appropriate directories.
This will ensure proper test organization while maintaining pytest compatibility.
"""

import os
import shutil
from pathlib import Path

# Define test categories and corresponding files
test_categories = {
    "cli": ["test_cli.py"],
    "utils": [
        "test_utils.py",
        "test_token_counter.py",
        "test_version.py",
        "test_patterns.py",
        "test_sqlasync_io.py",
        "test_settings.py",
        "test_logging_config.py",
    ],
    "core": [
        "test_validator.py",
        "test_schemas.py",
        "test_main.py",
        "test_config_loader.py",
        "test_errors.py",
        "test_secure_config.py",
    ],
    "tagging": ["test_tags.py", "test_tagging.py"],
    "search": [
        "test_search_engine.py",
        "test_similarity_search.py",
        "test_similarity_provider.py",
        "test_search_engine_similarity.py",
        "test_regex_provider.py",
    ],
    "ingest": ["test_ingest.py", "test_ingest_reader.py"],
    "relationships": ["test_relationship.py", "test_relationship_store.py"],
    "file_operations": [
        "test_file_watcher.py",
        "test_async_changes.py",
        "test_file_mover.py",
        "test_file_metadata.py",
        "test_directory_manager.py",
    ],
    "output": ["test_html_writer.py", "test_csv_writer.py"],
    "content_processing": [
        "test_code_summary.py",
        "test_notebook_converter.py",
        "test_ocr_parser.py",
        "test_archive_parser.py",
    ],
}

# Path to the tests directory
tests_dir = Path("backend/tests")
unit_dir = tests_dir / "unit"

# Create directories and __init__.py files
for category, _ in test_categories.items():
    category_dir = unit_dir / category
    os.makedirs(category_dir, exist_ok=True)

    # Create __init__.py in each directory
    init_file = category_dir / "__init__.py"
    if not init_file.exists():
        with open(init_file, "w") as f:
            f.write("# Initialize test package\n")

# Create integration test directory
integration_dir = tests_dir / "integration"
os.makedirs(integration_dir, exist_ok=True)
with open(integration_dir / "__init__.py", "w") as f:
    f.write("# Initialize integration test package\n")

# Move files to their respective directories
for category, files in test_categories.items():
    category_dir = unit_dir / category
    for file in files:
        source = tests_dir / file
        target = category_dir / file
        if source.exists() and not target.exists():
            try:
                shutil.copy2(source, target)
                print(f"Copied {file} to {category_dir}")
            except Exception as e:
                print(f"Error copying {file}: {e}")
        else:
            if not source.exists():
                print(f"Source file {source} does not exist")
            elif target.exists():
                print(f"Target file {target} already exists")

# Special test files that don't fit into categories
special_files = ["add_noqa.py", "conftest.py", "__init__.py"]
for file in special_files:
    source = tests_dir / file
    if source.exists():
        print(f"Keeping {file} in the root tests directory")

print(
    "\nTest organization complete. Files have been copied to their respective directories."
)
print("The original files still exist in the tests directory for reference.")
print("Once you've verified everything works, you can delete the original test files.")
