"""Handles file movement and organization based on predefined rules."""

import logging
import shutil
from pathlib import Path

from aichemist_codex.config.rules_engine import rules_engine
from aichemist_codex.utils.safety import SafeFileHandler

logger = logging.getLogger(__name__)


class FileMover:
    """Class for managing file movement and applying rules."""

    def __init__(self, base_directory: Path):
        self.base_directory = base_directory
        self.safe_scanner = SafeFileHandler

    def move_file(source: Path, destination: Path):
        """Moves a file to a new directory, creating it if needed."""
        if SafeFileHandler.should_ignore(source):
            logger.info(f"Skipping ignored file: {source}")
            return

        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(destination))
            logger.info(f"Moved {source} -> {destination}")
        except Exception as e:
            logger.error(f"Error moving {source}: {e}")

    def apply_rules(self, file_path: Path):
        """Determines if a file should be moved based on rules."""
        for rule in rules_engine.rules:
            if any(file_path.suffix == ext for ext in rule.get("extensions", [])):
                target_dir = Path(rule["target_dir"])
                self.move_file(file_path, target_dir / file_path.name)
