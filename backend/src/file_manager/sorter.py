import asyncio
import fnmatch
import logging
from pathlib import Path

import yaml

from file_manager import directory_manager, file_mover
from utils import AsyncFileIO

logger = logging.getLogger(__name__)


class RuleBasedSorter:
    def __init__(self):
        # Remove the synchronous load_rules call; rules will be loaded asynchronously.
        self.rules = None

    async def load_rules(self):
        config_dir = Path(__file__).resolve().parent.parent / "config"
        rules_file = config_dir / "sorting_rules.yaml"
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

    async def sort_directory(self, directory: Path):
        if self.rules is None:
            self.rules = await self.load_rules()
        for file in directory.rglob("*"):
            if file.is_file():
                for rule in self.rules:
                    if self.rule_matches(file, rule):
                        target_dir = Path(rule.get("target_dir"))
                        if not target_dir.is_absolute():
                            target_dir = directory / target_dir
                        # Skip the file if it's already in the target directory.
                        if file.parent == target_dir:
                            continue
                        await directory_manager.DirectoryManager.ensure_directory(
                            target_dir
                        )
                        logger.info(f"Applying rule {rule} to file {file}")
                        await file_mover.FileMover(directory).move_file(
                            file, target_dir / file.name
                        )
                        break

    # Optional: Provide a synchronous wrapper if needed.
    def sort_directory_sync(self, directory: Path):
        asyncio.run(self.sort_directory(directory))
