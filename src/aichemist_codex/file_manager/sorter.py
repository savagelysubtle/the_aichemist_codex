import fnmatch
import logging
from pathlib import Path

import yaml

from aichemist_codex.file_manager.directory_manager import DirectoryManager
from aichemist_codex.file_manager.file_mover import FileMover

logger = logging.getLogger(__name__)


class RuleBasedSorter:
    def __init__(self):
        self.rules = self.load_rules()

    def load_rules(self):
        # Load sorting rules from sorting_rules.yaml in the config directory
        config_dir = Path(__file__).resolve().parent.parent / "config"
        rules_file = config_dir / "sorting_rules.yaml"
        if not rules_file.exists():
            logger.warning(
                f"Sorting rules file not found at {rules_file}. No rules loaded."
            )
            return []
        try:
            with open(rules_file, "r", encoding="utf-8") as f:
                rules_data = yaml.safe_load(f)
            return rules_data.get("rules", [])
        except Exception as e:
            logger.error(f"Error loading sorting rules: {e}")
            return []

    def rule_matches(self, file_path: Path, rule: dict) -> bool:
        # Check match using filename pattern and extension criteria.
        pattern = rule.get("pattern")
        if pattern and not fnmatch.fnmatch(file_path.name, pattern):
            return False
        extensions = rule.get("extensions")
        if extensions and file_path.suffix.lower() not in [
            ext.lower() for ext in extensions
        ]:
            return False
        # Additional criteria (metadata, keywords) can be added here.
        return True

    def sort_directory(self, directory: Path):
        # Recursively apply sorting rules to files.
        for file in directory.rglob("*"):
            if file.is_file():
                for rule in self.rules:
                    if self.rule_matches(file, rule):
                        target_dir = Path(rule.get("target_dir"))
                        if not target_dir.is_absolute():
                            target_dir = directory / target_dir
                        DirectoryManager.ensure_directory(target_dir)
                        logger.info(f"Applying rule {rule} to file {file}")
                        FileMover.move_file(file, target_dir / file.name)
                        break  # Stop after first matching rule.
