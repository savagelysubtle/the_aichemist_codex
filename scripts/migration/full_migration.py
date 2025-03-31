#!/usr/bin/env python
"""
AIchemist Codex Comprehensive Migration Script

This script executes a complete migration of the AIchemist Codex codebase
from the legacy structure to the new clean architecture. It includes:

- Comprehensive component mapping
- Directory structure creation
- File migration with import updates
- Validation of migrated code
- Detailed reporting
- Rollback capabilities

Usage:
    python full_migration.py [--dry-run] [--validate-only] [--rollback]

Features:
    - Complete codebase restructuring
    - Automatic import statement updates
    - Validation of migrated code
    - Comprehensive logging
    - Rollback support
    - Detailed reporting
"""

import argparse
import json
import logging
import re
import shutil
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

# Configure logging
log_file = f"migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_file),
    ],
)
logger = logging.getLogger(__name__)


# Define the operation types
class OperationType(Enum):
    """Types of operations supported by the script."""

    CREATE_DIRECTORY = "create_directory"
    CREATE_FILE = "create_file"
    MOVE = "move"
    COPY = "copy"
    MERGE = "merge"
    DELETE = "delete"
    REFACTOR = "refactor"


class RefactorOperationType(Enum):
    """Types of refactoring operations."""

    REPLACE_IMPORT = "replace_import"
    REPLACE_TEXT = "replace_text"
    RENAME_CLASS = "rename_class"
    RENAME_FUNCTION = "rename_function"
    UPDATE_CLASS_INHERITANCE = "update_class_inheritance"


@dataclass
class Operation:
    """Base class for all operations."""

    type: OperationType
    path: str | None = None
    source: str | None = None
    destination: str | None = None
    content_template: str | None = None
    merge: bool = False
    operations: list[dict[str, Any]] = field(default_factory=list)
    completed: bool = False
    error: str | None = None

    def validate(self, project_root: Path) -> bool:
        """Validate the operation."""
        if self.type == OperationType.CREATE_DIRECTORY:
            return self.path is not None
        elif self.type == OperationType.CREATE_FILE:
            return self.path is not None and self.content_template is not None
        elif self.type == OperationType.MOVE or self.type == OperationType.COPY:
            return self.source is not None and self.destination is not None
        elif self.type == OperationType.MERGE:
            return self.source is not None and self.destination is not None
        elif self.type == OperationType.DELETE:
            return self.path is not None
        elif self.type == OperationType.REFACTOR:
            return self.path is not None and len(self.operations) > 0
        return False

    def apply(self, project_root: Path, dry_run: bool = False) -> bool:
        """Apply the operation."""
        logger.info(
            f"Applying operation: {self.type.value} to {self.path or self.destination}"
        )
        return True


class MigrationReport:
    """Class for generating migration reports."""

    def __init__(self):
        self.start_time = datetime.now()
        self.operations_total = 0
        self.operations_completed = 0
        self.operations_failed = 0
        self.created_directories = []
        self.created_files = []
        self.moved_files = []
        self.copied_files = []
        self.merged_files = []
        self.deleted_files = []
        self.refactored_files = []
        self.errors = []

    def add_operation_result(
        self, operation: Operation, success: bool, error: str | None = None
    ):
        """Add an operation result to the report."""
        self.operations_total += 1
        if success:
            self.operations_completed += 1
            if operation.type == OperationType.CREATE_DIRECTORY:
                self.created_directories.append(operation.path)
            elif operation.type == OperationType.CREATE_FILE:
                self.created_files.append(operation.path)
            elif operation.type == OperationType.MOVE:
                self.moved_files.append((operation.source, operation.destination))
            elif operation.type == OperationType.COPY:
                self.copied_files.append((operation.source, operation.destination))
            elif operation.type == OperationType.MERGE:
                self.merged_files.append((operation.source, operation.destination))
            elif operation.type == OperationType.DELETE:
                self.deleted_files.append(operation.path)
            elif operation.type == OperationType.REFACTOR:
                self.refactored_files.append(operation.path)
        else:
            self.operations_failed += 1
            self.errors.append((operation, error))

    def generate_report(self) -> str:
        """Generate a report of the migration."""
        end_time = datetime.now()
        duration = end_time - self.start_time

        report = [
            "=" * 80,
            f"AIchemist Codex Migration Report - {end_time.strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 80,
            f"Duration: {duration}",
            f"Operations Total: {self.operations_total}",
            f"Operations Completed: {self.operations_completed}",
            f"Operations Failed: {self.operations_failed}",
            f"Success Rate: {(self.operations_completed / self.operations_total) * 100:.2f}%",
            "",
            f"Created Directories: {len(self.created_directories)}",
            f"Created Files: {len(self.created_files)}",
            f"Moved Files: {len(self.moved_files)}",
            f"Copied Files: {len(self.copied_files)}",
            f"Merged Files: {len(self.merged_files)}",
            f"Deleted Files: {len(self.deleted_files)}",
            f"Refactored Files: {len(self.refactored_files)}",
            "",
            "Failed Operations:",
        ]

        for operation, error in self.errors:
            report.append(
                f"  - {operation.type.value}: {operation.path or operation.destination} - {error}"
            )

        return "\n".join(report)

    def save_report(self, path: str):
        """Save the report to a file."""
        with open(path, "w") as f:
            f.write(self.generate_report())


class MigrationManager:
    """Class for managing the migration process."""

    def __init__(self, project_root: str, config_file: str, dry_run: bool = False):
        self.project_root = Path(project_root)
        self.config_file = config_file
        self.dry_run = dry_run
        self.operations = []
        self.backup_dir = None
        self.report = MigrationReport()

    def load_config(self):
        """Load the configuration file."""
        logger.info(f"Loading configuration from {self.config_file}")
        with open(self.config_file) as f:
            config = json.load(f)

        # Validate the configuration
        if "version" not in config:
            raise ValueError("Configuration file is missing 'version' field")
        if "operations" not in config:
            raise ValueError("Configuration file is missing 'operations' field")

        logger.info(f"Loaded configuration version {config['version']}")
        logger.info(f"Found {len(config['operations'])} operations")

        # Parse operations
        for op_data in config["operations"]:
            op_type = OperationType(op_data["type"])
            operation = Operation(
                type=op_type,
                path=op_data.get("path"),
                source=op_data.get("source"),
                destination=op_data.get("destination"),
                content_template=op_data.get("content_template"),
                merge=op_data.get("merge", False),
                operations=op_data.get("operations", []),
            )
            self.operations.append(operation)

        logger.info(f"Parsed {len(self.operations)} operations")
        return config

    def validate_operations(self):
        """Validate all operations."""
        logger.info("Validating operations")
        invalid_operations = []

        for operation in self.operations:
            if not operation.validate(self.project_root):
                invalid_operations.append(operation)

        if invalid_operations:
            logger.error(f"Found {len(invalid_operations)} invalid operations:")
            for op in invalid_operations:
                logger.error(f"  - {op.type.value}: {op.path or op.destination}")
            raise ValueError(f"Found {len(invalid_operations)} invalid operations")

        logger.info("All operations validated successfully")

    def create_backup(self):
        """Create a backup of the project."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backup_dir = self.project_root.parent / f"backup_{timestamp}"
        logger.info(f"Creating backup at {self.backup_dir}")

        if not self.dry_run:
            shutil.copytree(self.project_root, self.backup_dir)
            logger.info("Backup created successfully")
        else:
            logger.info("Dry run: Skipping backup creation")

    def execute_migration(self):
        """Execute the migration."""
        logger.info("Starting migration execution")

        # Create directories first
        for operation in [
            op for op in self.operations if op.type == OperationType.CREATE_DIRECTORY
        ]:
            try:
                success = self._execute_create_directory(operation)
                self.report.add_operation_result(operation, success)
            except Exception as e:
                logger.error(f"Error executing {operation.type.value}: {str(e)}")
                operation.error = str(e)
                self.report.add_operation_result(operation, False, str(e))

        # Create files next
        for operation in [
            op for op in self.operations if op.type == OperationType.CREATE_FILE
        ]:
            try:
                success = self._execute_create_file(operation)
                self.report.add_operation_result(operation, success)
            except Exception as e:
                logger.error(f"Error executing {operation.type.value}: {str(e)}")
                operation.error = str(e)
                self.report.add_operation_result(operation, False, str(e))

        # Then move files
        for operation in [
            op for op in self.operations if op.type == OperationType.MOVE
        ]:
            try:
                success = self._execute_move(operation)
                self.report.add_operation_result(operation, success)
            except Exception as e:
                logger.error(f"Error executing {operation.type.value}: {str(e)}")
                operation.error = str(e)
                self.report.add_operation_result(operation, False, str(e))

        # Copy files
        for operation in [
            op for op in self.operations if op.type == OperationType.COPY
        ]:
            try:
                success = self._execute_copy(operation)
                self.report.add_operation_result(operation, success)
            except Exception as e:
                logger.error(f"Error executing {operation.type.value}: {str(e)}")
                operation.error = str(e)
                self.report.add_operation_result(operation, False, str(e))

        # Merge files
        for operation in [
            op for op in self.operations if op.type == OperationType.MERGE
        ]:
            try:
                success = self._execute_merge(operation)
                self.report.add_operation_result(operation, success)
            except Exception as e:
                logger.error(f"Error executing {operation.type.value}: {str(e)}")
                operation.error = str(e)
                self.report.add_operation_result(operation, False, str(e))

        # Refactor files
        for operation in [
            op for op in self.operations if op.type == OperationType.REFACTOR
        ]:
            try:
                success = self._execute_refactor(operation)
                self.report.add_operation_result(operation, success)
            except Exception as e:
                logger.error(f"Error executing {operation.type.value}: {str(e)}")
                operation.error = str(e)
                self.report.add_operation_result(operation, False, str(e))

        # Finally delete files
        for operation in [
            op for op in self.operations if op.type == OperationType.DELETE
        ]:
            try:
                success = self._execute_delete(operation)
                self.report.add_operation_result(operation, success)
            except Exception as e:
                logger.error(f"Error executing {operation.type.value}: {str(e)}")
                operation.error = str(e)
                self.report.add_operation_result(operation, False, str(e))

        logger.info("Migration execution completed")

    def _execute_create_directory(self, operation: Operation) -> bool:
        """Execute a create directory operation."""
        if operation.path is None:
            return False

        dir_path = self.project_root / operation.path
        logger.info(f"Creating directory: {dir_path}")

        if not self.dry_run:
            dir_path.mkdir(parents=True, exist_ok=True)

        operation.completed = True
        return True

    def _execute_create_file(self, operation: Operation) -> bool:
        """Execute a create file operation."""
        if operation.path is None or operation.content_template is None:
            return False

        file_path = self.project_root / operation.path
        logger.info(f"Creating file: {file_path}")

        # Make sure the parent directory exists
        if not self.dry_run:
            file_path.parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, "w") as f:
                f.write(operation.content_template)

        operation.completed = True
        return True

    def _execute_move(self, operation: Operation) -> bool:
        """Execute a move operation."""
        if operation.source is None or operation.destination is None:
            return False

        source_path = self.project_root / operation.source
        dest_path = self.project_root / operation.destination
        logger.info(f"Moving file: {source_path} -> {dest_path}")

        if not source_path.exists():
            logger.warning(f"Source file not found: {source_path}")
            operation.error = f"Source file not found: {source_path}"
            return False

        if not self.dry_run:
            # Make sure the parent directory exists
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            # Move the file
            shutil.move(source_path, dest_path)

        operation.completed = True
        return True

    def _execute_copy(self, operation: Operation) -> bool:
        """Execute a copy operation."""
        if operation.source is None or operation.destination is None:
            return False

        source_path = self.project_root / operation.source
        dest_path = self.project_root / operation.destination
        logger.info(f"Copying file: {source_path} -> {dest_path}")

        if not source_path.exists():
            logger.warning(f"Source file not found: {source_path}")
            operation.error = f"Source file not found: {source_path}"
            return False

        if not self.dry_run:
            # Make sure the parent directory exists
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            # Copy the file
            shutil.copy2(source_path, dest_path)

        operation.completed = True
        return True

    def _execute_merge(self, operation: Operation) -> bool:
        """Execute a merge operation."""
        if operation.source is None or operation.destination is None:
            return False

        source_path = self.project_root / operation.source
        dest_path = self.project_root / operation.destination
        logger.info(f"Merging file: {source_path} -> {dest_path}")

        if not source_path.exists():
            logger.warning(f"Source file not found: {source_path}")
            operation.error = f"Source file not found: {source_path}"
            return False

        if not self.dry_run:
            # Make sure the parent directory exists
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            # Read source content
            with open(source_path) as f:
                source_content = f.read()

            # If destination exists, append to it, otherwise create it
            if dest_path.exists():
                with open(dest_path, "a") as f:
                    f.write(
                        "\n\n# Merged from "
                        + str(source_path.relative_to(self.project_root))
                        + "\n"
                    )
                    f.write(source_content)
            else:
                with open(dest_path, "w") as f:
                    f.write(source_content)

        operation.completed = True
        return True

    def _execute_delete(self, operation: Operation) -> bool:
        """Execute a delete operation."""
        if operation.path is None:
            return False

        file_path = self.project_root / operation.path
        logger.info(f"Deleting file: {file_path}")

        if not file_path.exists():
            logger.warning(f"File not found: {file_path}")
            operation.error = f"File not found: {file_path}"
            return False

        if not self.dry_run:
            if file_path.is_dir():
                shutil.rmtree(file_path)
            else:
                file_path.unlink()

        operation.completed = True
        return True

    def _execute_refactor(self, operation: Operation) -> bool:
        """Execute a refactor operation."""
        if operation.path is None or not operation.operations:
            return False

        file_path = self.project_root / operation.path
        logger.info(f"Refactoring file: {file_path}")

        if not file_path.exists():
            logger.warning(f"File not found: {file_path}")
            operation.error = f"File not found: {file_path}"
            return False

        if not self.dry_run:
            # Read the file content
            with open(file_path) as f:
                content = f.read()

            # Apply refactoring operations
            for refactor_op in operation.operations:
                refactor_type = RefactorOperationType(refactor_op["type"])

                if refactor_type == RefactorOperationType.REPLACE_IMPORT:
                    old_import = refactor_op["old"]
                    new_import = refactor_op["new"]
                    content = content.replace(old_import, new_import)
                    logger.info(f"  Replaced import: {old_import} -> {new_import}")

                elif refactor_type == RefactorOperationType.REPLACE_TEXT:
                    old_text = refactor_op["old"]
                    new_text = refactor_op["new"]
                    content = content.replace(old_text, new_text)
                    logger.info(f"  Replaced text: {old_text} -> {new_text}")

                elif refactor_type == RefactorOperationType.RENAME_CLASS:
                    old_class = refactor_op["old"]
                    new_class = refactor_op["new"]
                    pattern = r"\bclass\s+" + re.escape(old_class) + r"\b"
                    content = re.sub(pattern, f"class {new_class}", content)
                    logger.info(f"  Renamed class: {old_class} -> {new_class}")

                elif refactor_type == RefactorOperationType.RENAME_FUNCTION:
                    old_function = refactor_op["old"]
                    new_function = refactor_op["new"]
                    pattern = r"\bdef\s+" + re.escape(old_function) + r"\b"
                    content = re.sub(pattern, f"def {new_function}", content)
                    logger.info(f"  Renamed function: {old_function} -> {new_function}")

                elif refactor_type == RefactorOperationType.UPDATE_CLASS_INHERITANCE:
                    class_name = refactor_op["class"]
                    old_base = refactor_op["old_base"]
                    new_base = refactor_op["new_base"]
                    pattern = (
                        r"\bclass\s+"
                        + re.escape(class_name)
                        + r"\s*\(\s*"
                        + re.escape(old_base)
                        + r"\s*\)"
                    )
                    content = re.sub(
                        pattern, f"class {class_name}({new_base})", content
                    )
                    logger.info(
                        f"  Updated class inheritance: {class_name}({old_base}) -> {class_name}({new_base})"
                    )

            # Write the updated content back to the file
            with open(file_path, "w") as f:
                f.write(content)

        operation.completed = True
        return True

    def generate_report(self):
        """Generate a report of the migration."""
        report_path = f"migration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        logger.info(f"Generating migration report at {report_path}")

        self.report.save_report(report_path)

        return report_path

    def rollback(self):
        """Rollback the migration."""
        if self.backup_dir is None:
            logger.error("No backup available for rollback")
            return False

        logger.info(f"Rolling back migration from backup: {self.backup_dir}")

        if not self.dry_run:
            # Remove the current project
            shutil.rmtree(self.project_root)

            # Restore from backup
            shutil.copytree(self.backup_dir, self.project_root)

            logger.info("Rollback completed successfully")
        else:
            logger.info("Dry run: Skipping rollback execution")

        return True

    def validate_migration(self):
        """Validate the migration."""
        logger.info("Validating migration")

        # Count successful operations vs total
        success_rate = (
            self.report.operations_completed / self.report.operations_total
        ) * 100
        logger.info(f"Success rate: {success_rate:.2f}%")

        # Check that all expected files exist
        missing_files = []
        for operation in self.operations:
            if operation.type == OperationType.CREATE_FILE and operation.completed:
                file_path = self.project_root / operation.path
                if not file_path.exists():
                    missing_files.append(operation.path)
            elif operation.type == OperationType.MOVE and operation.completed:
                dest_path = self.project_root / operation.destination
                if not dest_path.exists():
                    missing_files.append(operation.destination)

        if missing_files:
            logger.error(f"Found {len(missing_files)} missing files after migration:")
            for path in missing_files:
                logger.error(f"  - {path}")
            return False

        logger.info("Migration validation completed successfully")
        return True


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="AIchemist Codex Comprehensive Migration Script"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="scripts/migration/restructure_config.json",
        help="Path to the configuration file",
    )
    parser.add_argument(
        "--project-root",
        type=str,
        default=".",
        help="Path to the project root directory",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform a dry run without making any changes",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate the operations without executing them",
    )
    parser.add_argument(
        "--rollback",
        action="store_true",
        help="Rollback the migration if a backup is available",
    )
    return parser.parse_args()


def main():
    """Main function."""
    args = parse_args()

    project_root = args.project_root
    config_file = args.config
    dry_run = args.dry_run
    validate_only = args.validate_only
    rollback = args.rollback

    logger.info("Starting AIchemist Codex migration")
    logger.info(f"Project root: {project_root}")
    logger.info(f"Config file: {config_file}")
    logger.info(f"Dry run: {dry_run}")
    logger.info(f"Validate only: {validate_only}")
    logger.info(f"Rollback: {rollback}")

    try:
        manager = MigrationManager(project_root, config_file, dry_run)

        # Load and validate the configuration
        manager.load_config()
        manager.validate_operations()

        if validate_only:
            logger.info("Validation completed successfully")
            return 0

        if rollback:
            success = manager.rollback()
            return 0 if success else 1

        # Create a backup
        manager.create_backup()

        # Execute the migration
        manager.execute_migration()

        # Generate a report
        report_path = manager.generate_report()

        # Validate the migration
        if not dry_run:
            success = manager.validate_migration()
            if not success:
                logger.error("Migration validation failed")
                if not input("Continue anyway? (y/n): ").lower().startswith("y"):
                    logger.info("Rolling back migration")
                    manager.rollback()
                    return 1

        logger.info(
            f"Migration completed successfully. Report available at {report_path}"
        )
        return 0

    except Exception as e:
        logger.exception(f"Error during migration: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
