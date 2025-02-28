import asyncio
import fnmatch
import logging
from pathlib import Path

import yaml

from aichemist_codex.file_manager import directory_manager, file_mover

logger = logging.getLogger(__name__)


class RuleBasedSorter:
    def __init__(self):
        self.rules = asyncio.run(self.load_rules())

    async def load_rules(self):
        config_dir = Path(__file__).resolve().parent.parent / "config"
        rules_file = config_dir / "sorting_rules.yaml"
        from aichemist_codex.utils import AsyncFileIO

        if not await AsyncFileIO.exists(rules_file):
            logger.warning(
                f"Sorting rules file not found at {rules_file}. No rules loaded."
            )
            return []
        try:
            content = await AsyncFileIO.read(rules_file)
            rules_data = yaml.safe_load(content)
            return rules_data.get("rules", [])
        except Exception as e:
            logger.error(f"Error loading sorting rules: {e}")
            return []

    def rule_matches(self, file_path: Path, rule: dict) -> bool:
        pattern = rule.get("pattern")
        if pattern and not fnmatch.fnmatch(file_path.name, pattern):
            return False
        extensions = rule.get("extensions")
        if extensions and file_path.suffix.lower() not in [
            ext.lower() for ext in extensions
        ]:
            return False
        return True

    async def _sort_directory(self, directory: Path):
        for file in directory.rglob("*"):
            if file.is_file():
                for rule in self.rules:
                    if self.rule_matches(file, rule):
                        target_dir = Path(rule.get("target_dir"))
                        if not target_dir.is_absolute():
                            target_dir = directory / target_dir
                        await directory_manager.DirectoryManager.ensure_directory(
                            target_dir
                        )
                        logger.info(f"Applying rule {rule} to file {file}")
                        await file_mover.FileMover(directory).move_file(
                            file, target_dir / file.name
                        )
                        break

    def sort_directory(self, directory: Path):
        asyncio.run(self._sort_directory(directory))
