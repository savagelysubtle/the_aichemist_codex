#!/usr/bin/env python
"""
Codebase Restructuring Script

This script automates the restructuring of the AIchemist Codex codebase
by processing a JSON configuration file that defines file and directory
operations such as creation, movement, copying, and refactoring.

Usage:
    python codebase_restructure.py --config path/to/config.json [--dry-run] [--verbose]

Features:
    - Directory creation
    - File creation
    - File movement and copying
    - Content merging with regex patterns
    - Code refactoring (import updates, etc.)
    - Dry-run capability
    - Detailed logging
    - Rollback support
"""

import argparse
import json
import logging
import os
import re
import shutil
import sys
import tempfile
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("codebase_restructure.log"),
    ],
)
logger = logging.getLogger(__name__)


class OperationType(Enum):
    """Types of operations supported by the script."""

    CREATE_DIRECTORY = "create_directory"
    CREATE_FILE = "create_file"
    MOVE = "move"
    COPY = "copy"
    MERGE = "merge"
    REFACTOR = "refactor"
    DELETE = "delete"


@dataclass
class Operation:
    """Base class for all operations."""

    type: OperationType
    path: str | None = None

    def validate(self, project_root: Path) -> bool:
        """Validate the operation parameters."""
        return True

    def execute(self, project_root: Path, dry_run: bool = False) -> bool:
        """Execute the operation."""
        raise NotImplementedError("Subclasses must implement execute")

    def rollback(self, project_root: Path) -> bool:
        """Rollback the operation."""
        raise NotImplementedError("Subclasses must implement rollback")


@dataclass
class CreateDirectoryOperation(Operation):
    """Operation to create a directory."""

    type: OperationType = OperationType.CREATE_DIRECTORY

    def validate(self, project_root: Path) -> bool:
        if not self.path:
            logger.error("Path is required for CREATE_DIRECTORY operation")
            return False
        return True

    def execute(self, project_root: Path, dry_run: bool = False) -> bool:
        if not self.path:  # Added null check
            return False

        target_path = project_root / self.path
        if dry_run:
            logger.info(f"[DRY RUN] Would create directory: {target_path}")
            return True

        try:
            target_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {target_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to create directory {target_path}: {e}")
            return False

    def rollback(self, project_root: Path) -> bool:
        if not self.path:  # Added null check
            return False

        target_path = project_root / self.path
        try:
            # Only remove if empty
            if target_path.exists() and not any(target_path.iterdir()):
                target_path.rmdir()
                logger.info(f"Removed empty directory: {target_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to rollback directory creation {target_path}: {e}")
            return False


@dataclass
class CreateFileOperation(Operation):
    """Operation to create a file."""

    type: OperationType = OperationType.CREATE_FILE
    content_template: str = ""

    def validate(self, project_root: Path) -> bool:
        if not self.path:
            logger.error("Path is required for CREATE_FILE operation")
            return False
        return True

    def execute(self, project_root: Path, dry_run: bool = False) -> bool:
        if not self.path:  # Added null check
            return False

        target_path = project_root / self.path

        if dry_run:
            logger.info(f"[DRY RUN] Would create file: {target_path}")
            logger.debug(f"With content: {self.content_template[:100]}...")
            return True

        try:
            # Create parent directories if they don't exist
            target_path.parent.mkdir(parents=True, exist_ok=True)

            # Write the file
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(self.content_template)

            logger.info(f"Created file: {target_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to create file {target_path}: {e}")
            return False

    def rollback(self, project_root: Path) -> bool:
        if not self.path:  # Added null check
            return False

        target_path = project_root / self.path
        try:
            if target_path.exists():
                target_path.unlink()
                logger.info(f"Removed file: {target_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to rollback file creation {target_path}: {e}")
            return False


@dataclass
class MoveOperation(Operation):
    """Operation to move a file."""

    type: OperationType = OperationType.MOVE
    source: str = ""
    destination: str = ""
    merge: bool = False
    merge_pattern: dict[str, Any] = field(default_factory=dict)  # Fixed initialization
    backup_path: str | None = None  # For rollback

    def validate(self, project_root: Path) -> bool:
        if not self.source or not self.destination:
            logger.error("Source and destination are required for MOVE operation")
            return False

        source_path = project_root / self.source
        if not source_path.exists():
            logger.error(f"Source file does not exist: {source_path}")
            return False

        if self.merge and not self.merge_pattern:
            logger.warning(
                f"Merge is set to True but no merge pattern provided for {self.source}"
            )

        return True

    def _extract_content(self, source_path: Path) -> str:
        """Extract content based on the merge pattern."""
        if not self.merge_pattern or "extract" not in self.merge_pattern:
            with open(source_path, encoding="utf-8") as f:
                return f.read()

        with open(source_path, encoding="utf-8") as f:
            content = f.read()

        pattern = self.merge_pattern["extract"]
        match = re.search(pattern, content, re.DOTALL)
        if match:
            return match.group(0)

        logger.warning(
            f"Could not extract content using pattern '{pattern}' from {source_path}"
        )
        return ""

    def execute(self, project_root: Path, dry_run: bool = False) -> bool:
        source_path = project_root / self.source
        dest_path = project_root / self.destination

        if dry_run:
            if self.merge:
                logger.info(f"[DRY RUN] Would merge {source_path} into {dest_path}")
            else:
                logger.info(f"[DRY RUN] Would move {source_path} to {dest_path}")
            return True

        try:
            # Create parent directories if needed
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            # Create backup for rollback if needed
            if source_path.exists():
                backup_dir = project_root / ".restructure_backup"
                backup_dir.mkdir(exist_ok=True)
                self.backup_path = str(backup_dir / source_path.name)
                shutil.copy2(source_path, self.backup_path)

            if self.merge and dest_path.exists():
                # Merge operation
                extracted_content = self._extract_content(source_path)

                with open(dest_path, encoding="utf-8") as f:
                    existing_content = f.read()

                # Determine merge strategy
                if self.merge_pattern and self.merge_pattern.get("append", True):
                    new_content = existing_content.rstrip() + "\n\n" + extracted_content
                else:
                    new_content = extracted_content + "\n\n" + existing_content

                with open(dest_path, "w", encoding="utf-8") as f:
                    f.write(new_content)

                logger.info(f"Merged content from {source_path} into {dest_path}")

                # Remove the source file after merging
                source_path.unlink()
                logger.info(f"Removed source file after merge: {source_path}")
            else:
                # Simple move operation
                if dest_path.exists():
                    # Backup the destination file
                    backup_dir = project_root / ".restructure_backup"
                    backup_dir.mkdir(exist_ok=True)
                    dest_backup = backup_dir / f"{dest_path.name}.bak"
                    shutil.copy2(dest_path, dest_backup)

                shutil.move(source_path, dest_path)
                logger.info(f"Moved {source_path} to {dest_path}")

            return True
        except Exception as e:
            logger.error(f"Failed to move {source_path} to {dest_path}: {e}")
            return False

    def rollback(self, project_root: Path) -> bool:
        source_path = project_root / self.source
        dest_path = project_root / self.destination

        try:
            if self.backup_path and Path(self.backup_path).exists():
                # Restore from backup
                shutil.copy2(self.backup_path, source_path)
                logger.info(f"Restored {source_path} from backup")

                if self.merge and dest_path.exists():
                    # Attempt to undo merge (this is tricky and not always perfect)
                    logger.warning(
                        f"Attempting to rollback merge for {dest_path}, but contents may not be fully restored"
                    )
                    # This is simplified and may not work for all cases
                    extracted_content = self._extract_content(Path(self.backup_path))
                    with open(dest_path, encoding="utf-8") as f:
                        content = f.read()

                    new_content = content.replace(extracted_content, "").replace(
                        "\n\n\n", "\n\n"
                    )
                    with open(dest_path, "w", encoding="utf-8") as f:
                        f.write(new_content)
            elif not self.merge:
                # Try to move the destination back to source if it exists
                if dest_path.exists() and not source_path.exists():
                    source_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(dest_path, source_path)
                    logger.info(f"Moved {dest_path} back to {source_path}")

            return True
        except Exception as e:
            logger.error(f"Failed to rollback move operation: {e}")
            return False


@dataclass
class CopyOperation(Operation):
    """Operation to copy a file."""

    type: OperationType = OperationType.COPY
    source: str = ""
    destination: str = ""

    def validate(self, project_root: Path) -> bool:
        if not self.source or not self.destination:
            logger.error("Source and destination are required for COPY operation")
            return False

        source_path = project_root / self.source
        if not source_path.exists():
            logger.error(f"Source file does not exist: {source_path}")
            return False

        return True

    def execute(self, project_root: Path, dry_run: bool = False) -> bool:
        source_path = project_root / self.source
        dest_path = project_root / self.destination

        if dry_run:
            logger.info(f"[DRY RUN] Would copy {source_path} to {dest_path}")
            return True

        try:
            # Create parent directories if needed
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            shutil.copy2(source_path, dest_path)
            logger.info(f"Copied {source_path} to {dest_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to copy {source_path} to {dest_path}: {e}")
            return False

    def rollback(self, project_root: Path) -> bool:
        dest_path = project_root / self.destination

        try:
            if dest_path.exists():
                dest_path.unlink()
                logger.info(f"Removed copied file: {dest_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to rollback copy operation: {e}")
            return False


@dataclass
class RefactorOperation(Operation):
    """Operation to refactor code."""

    type: OperationType = OperationType.REFACTOR
    operations: list[dict[str, Any]] = field(
        default_factory=list
    )  # Fixed initialization
    backup_content: str | None = None  # For rollback

    def validate(self, project_root: Path) -> bool:
        if not self.path:
            logger.error("Path is required for REFACTOR operation")
            return False

        if not self.operations:
            logger.error("Refactor operations are required")
            return False

        target_path = project_root / self.path
        if not target_path.exists():
            logger.error(f"Target file does not exist: {target_path}")
            return False

        return True

    def execute(self, project_root: Path, dry_run: bool = False) -> bool:
        if not self.path:  # Added null check
            return False

        target_path = project_root / self.path

        if dry_run:
            logger.info(f"[DRY RUN] Would refactor {target_path}")
            for op in self.operations:
                logger.info(
                    f"  - {op['type']}: {op.get('old', '')} -> {op.get('new', '')}"
                )
            return True

        try:
            # Create backup for rollback
            with open(target_path, encoding="utf-8") as f:
                self.backup_content = f.read()

            # Read file content
            with open(target_path, encoding="utf-8") as f:
                content = f.read()

            # Apply refactoring operations
            for op in self.operations:
                if op["type"] == "replace_import":
                    old_import = op["old"]
                    new_import = op["new"]
                    content = re.sub(
                        rf"from\s+{re.escape(old_import)}\s+import",
                        f"from {new_import} import",
                        content,
                    )
                    content = re.sub(
                        rf"import\s+{re.escape(old_import)}",
                        f"import {new_import}",
                        content,
                    )
                elif op["type"] == "replace_text":
                    old_text = op["old"]
                    new_text = op["new"]
                    content = content.replace(old_text, new_text)
                elif op["type"] == "regex_replace":
                    pattern = op["pattern"]
                    replacement = op["replacement"]
                    content = re.sub(pattern, replacement, content, flags=re.DOTALL)

            # Write updated content
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(content)

            logger.info(f"Refactored {target_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to refactor {target_path}: {e}")
            return False

    def rollback(self, project_root: Path) -> bool:
        if not self.path:  # Added null check
            return False

        target_path = project_root / self.path

        try:
            if self.backup_content is not None:
                with open(target_path, "w", encoding="utf-8") as f:
                    f.write(self.backup_content)
                logger.info(f"Restored {target_path} to original content")
            return True
        except Exception as e:
            logger.error(f"Failed to rollback refactor operation: {e}")
            return False


@dataclass
class DeleteOperation(Operation):
    """Operation to delete a file or directory."""

    type: OperationType = OperationType.DELETE
    backup_path: str | None = None  # For rollback

    def validate(self, project_root: Path) -> bool:
        if not self.path:
            logger.error("Path is required for DELETE operation")
            return False

        target_path = project_root / self.path
        if not target_path.exists():
            logger.warning(f"Target does not exist, nothing to delete: {target_path}")

        return True

    def execute(self, project_root: Path, dry_run: bool = False) -> bool:
        if not self.path:  # Added null check
            return False

        target_path = project_root / self.path

        if not target_path.exists():
            logger.info(f"Target does not exist, skipping delete: {target_path}")
            return True

        if dry_run:
            logger.info(f"[DRY RUN] Would delete {target_path}")
            return True

        try:
            # Create backup for rollback
            backup_dir = project_root / ".restructure_backup"
            backup_dir.mkdir(exist_ok=True)

            if target_path.is_file():
                self.backup_path = str(backup_dir / target_path.name)
                shutil.copy2(target_path, self.backup_path)
                target_path.unlink()
                logger.info(f"Deleted file: {target_path}")
            else:
                # For directories, create a temporary backup
                temp_dir = tempfile.mkdtemp(dir=backup_dir)
                self.backup_path = temp_dir
                shutil.copytree(target_path, Path(temp_dir) / target_path.name)
                shutil.rmtree(target_path)
                logger.info(f"Deleted directory: {target_path}")

            return True
        except Exception as e:
            logger.error(f"Failed to delete {target_path}: {e}")
            return False

    def rollback(self, project_root: Path) -> bool:
        if not self.path:  # Added null check
            return False

        target_path = project_root / self.path

        try:
            if self.backup_path and Path(self.backup_path).exists():
                backup_path = Path(self.backup_path)

                if backup_path.is_file():
                    # Restore file
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(backup_path, target_path)
                    logger.info(f"Restored file: {target_path}")
                else:
                    # Restore directory
                    restored_path = list(Path(self.backup_path).iterdir())[
                        0
                    ]  # First item in temp dir
                    shutil.copytree(restored_path, target_path)
                    logger.info(f"Restored directory: {target_path}")

            return True
        except Exception as e:
            logger.error(f"Failed to rollback delete operation: {e}")
            return False


class CodebaseRestructurer:
    """Main class to handle the restructuring process."""

    def __init__(
        self, config_path: str, project_root: str | None = None
    ):  # Fixed type hint
        self.config_path = Path(config_path)
        self.project_root = Path(project_root or os.getcwd())
        self.operations = []
        self.executed_operations = []

    def load_config(self) -> bool:
        """Load the configuration file and parse operations."""
        try:
            with open(self.config_path, encoding="utf-8") as f:
                config = json.load(f)

            logger.info(f"Loaded configuration from {self.config_path}")
            logger.info(f"Description: {config.get('description', 'No description')}")
            logger.info(f"Version: {config.get('version', 'No version')}")

            # Parse operations
            for op_data in config.get("operations", []):
                op_type = op_data.get("type")

                if op_type == OperationType.CREATE_DIRECTORY.value:
                    op = CreateDirectoryOperation(
                        type=OperationType.CREATE_DIRECTORY, path=op_data.get("path")
                    )
                elif op_type == OperationType.CREATE_FILE.value:
                    op = CreateFileOperation(
                        type=OperationType.CREATE_FILE,
                        path=op_data.get("path"),
                        content_template=op_data.get("content_template", ""),
                    )
                elif op_type == OperationType.MOVE.value:
                    op = MoveOperation(
                        type=OperationType.MOVE,
                        path=op_data.get("destination"),  # For operation base class
                        source=op_data.get("source"),
                        destination=op_data.get("destination"),
                        merge=op_data.get("merge", False),
                        merge_pattern=op_data.get(
                            "merge_pattern", {}
                        ),  # Provide default
                    )
                elif op_type == OperationType.COPY.value:
                    op = CopyOperation(
                        type=OperationType.COPY,
                        path=op_data.get("destination"),  # For operation base class
                        source=op_data.get("source"),
                        destination=op_data.get("destination"),
                    )
                elif op_type == OperationType.REFACTOR.value:
                    op = RefactorOperation(
                        type=OperationType.REFACTOR,
                        path=op_data.get("path"),
                        operations=op_data.get("operations", []),  # Provide default
                    )
                elif op_type == OperationType.DELETE.value:
                    op = DeleteOperation(
                        type=OperationType.DELETE, path=op_data.get("path")
                    )
                else:
                    logger.warning(f"Unknown operation type: {op_type}, skipping")
                    continue

                self.operations.append(op)

            logger.info(f"Parsed {len(self.operations)} operations")
            return True
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            return False

    def validate_operations(self) -> bool:
        """Validate all operations before execution."""
        all_valid = True

        for i, op in enumerate(self.operations):
            if not op.validate(self.project_root):
                logger.error(f"Operation {i + 1} ({op.type.value}) validation failed")
                all_valid = False

        return all_valid

    def run(self, dry_run: bool = False) -> bool:
        """Execute all operations in sequence."""
        success = True
        self.executed_operations = []

        for i, op in enumerate(self.operations):
            logger.info(
                f"Executing operation {i + 1}/{len(self.operations)}: {op.type.value}"
            )

            if op.execute(self.project_root, dry_run):
                if not dry_run:
                    self.executed_operations.append(op)
            else:
                logger.error(f"Operation {i + 1} failed, stopping execution")
                success = False
                break

        if dry_run:
            logger.info("Dry run completed successfully")
        elif success:
            logger.info("All operations completed successfully")

        return success

    def rollback(self) -> bool:
        """Rollback all executed operations in reverse order."""
        if not self.executed_operations:
            logger.info("No operations to rollback")
            return True

        success = True

        for op in reversed(self.executed_operations):
            logger.info(f"Rolling back operation: {op.type.value}")

            if not op.rollback(self.project_root):
                logger.error(f"Failed to rollback operation: {op.type.value}")
                success = False

        if success:
            logger.info("All operations rolled back successfully")
        else:
            logger.warning("Some operations could not be rolled back")

        return success


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Codebase Restructuring Tool")
    parser.add_argument(
        "--config", "-c", required=True, help="Path to the JSON configuration file"
    )
    parser.add_argument(
        "--project-root",
        "-p",
        help="Path to the project root (defaults to current directory)",
    )
    parser.add_argument(
        "--dry-run",
        "-d",
        action="store_true",
        help="Perform a dry run without making changes",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    restructurer = CodebaseRestructurer(args.config, args.project_root)

    if not restructurer.load_config():
        logger.error("Failed to load configuration, exiting")
        return 1

    if not restructurer.validate_operations():
        logger.error("Operation validation failed, exiting")
        return 1

    try:
        if not restructurer.run(args.dry_run):
            logger.error("Execution failed")

            if not args.dry_run:
                logger.info("Attempting to rollback changes...")
                restructurer.rollback()

            return 1

        return 0
    except KeyboardInterrupt:
        logger.info("Operation interrupted by user")

        if not args.dry_run:
            logger.info("Attempting to rollback changes...")
            restructurer.rollback()

        return 130


if __name__ == "__main__":
    sys.exit(main())
