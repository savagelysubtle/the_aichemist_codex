import asyncio
import fnmatch
import logging
from datetime import datetime
from pathlib import Path

import yaml

# ? These imports reference your existing modules; adjust if your directory structure differs.
from file_manager.directory_manager import DirectoryManager as directory_manager
from file_manager.file_mover import FileMover as file_mover
from utils.async_io import AsyncFileIO

logger = logging.getLogger(__name__)


class RuleBasedSorter:
    """
    * RuleBasedSorter
    This class provides functionality to sort files based on a set of user-defined rules
    specified in a YAML file. It supports both basic matching (file name patterns, extensions)
    and extended matching (metadata filters, content keywords).

    Attributes:
        rules (list): A list of dictionaries, each representing a sorting rule.
    """

    def __init__(self):
        """
        * Initializes the sorter instance.

        ! By default, 'rules' is set to None. The actual rules are loaded asynchronously
        the first time 'sort_directory' is called, via 'load_rules'.
        """
        self.rules = None

    async def load_rules(self):
        """
        Loads the sorting rules from 'sorting_rules.yaml' in the config directory.

        * If the file is not found, it logs a warning and returns an empty list.
        * If the file is found, it attempts to parse the 'rules' key from the YAML.

        Returns:
            list: A list of rule dictionaries loaded from the YAML file.
        """
        config_dir = Path(__file__).resolve().parent.parent / "config"
        rules_file = config_dir / "sorting_rules.yaml"
        if not await AsyncFileIO.exists(rules_file):
            # ! Logging a warning because the rules file is missing.
            logger.warning(
                f"Sorting rules file not found at {rules_file}. No rules loaded."
            )
            return []
        try:
            content = await AsyncFileIO.read(rules_file)
            rules_data = yaml.safe_load(content)
            return rules_data.get("rules", [])
        except Exception as e:
            # ? Catching any parsing or IO errors to prevent crash.
            logger.error(f"Error loading sorting rules: {e}")
            return []

    def rule_matches(self, file_path: Path, rule: dict) -> bool:
        """
        Checks if a file matches the basic criteria of a given rule:
        name patterns and file extensions.

        * This method is synchronous and only checks for the 'pattern' and 'extensions' keys.

        Args:
            file_path (Path): The path of the file to check.
            rule (dict): A dictionary defining the sorting rule.

        Returns:
            bool: True if the file matches the pattern and/or extensions in the rule,
                  False otherwise.
        """
        pattern = rule.get("pattern")
        if pattern and not fnmatch.fnmatch(file_path.name, pattern):
            return False

        extensions = rule.get("extensions")
        if extensions and file_path.suffix.lower() not in [
            ext.lower() for ext in extensions
        ]:
            return False

        return True

    async def rule_matches_extended(self, file_path: Path, rule: dict) -> bool:
        """
        Asynchronously checks if a file matches extended criteria defined in a rule.

        * First, calls 'rule_matches' for basic pattern/extension checks.
        * Then, checks file size limits (min_size, max_size).
        * Next, checks file creation timestamps (created_after, created_before).
        * Finally, searches for any keywords in the file’s text content.

        Args:
            file_path (Path): The path of the file to check.
            rule (dict): A dictionary defining the sorting rule.

        Returns:
            bool: True if the file meets all criteria, False otherwise.
        """
        # ? Start with the basic rule matching.
        if not self.rule_matches(file_path, rule):
            return False

        try:
            stat = file_path.stat()
        except Exception as e:
            logger.error(f"Error getting stat for {file_path}: {e}")
            return False

        # * File size checks
        if "min_size" in rule:
            if stat.st_size < rule["min_size"]:
                return False
        if "max_size" in rule:
            if stat.st_size > rule["max_size"]:
                return False

        # * File creation timestamp checks
        if "created_after" in rule:
            try:
                after = datetime.fromisoformat(rule["created_after"])
                file_creation = datetime.fromtimestamp(stat.st_ctime)
                if file_creation < after:
                    return False
            except Exception as e:
                logger.error(f"Error parsing created_after for rule {rule}: {e}")
                return False

        if "created_before" in rule:
            try:
                before = datetime.fromisoformat(rule["created_before"])
                file_creation = datetime.fromtimestamp(stat.st_ctime)
                if file_creation > before:
                    return False
            except Exception as e:
                logger.error(f"Error parsing created_before for rule {rule}: {e}")
                return False

        # * Content keyword checks
        if "keywords" in rule:
            try:
                # ! Dynamically importing FileReader to avoid circular dependencies.
                from file_reader.file_reader import FileReader

                reader = FileReader()
                metadata = await reader.process_file(file_path)
                content = metadata.preview
                # TODO: If a rule has many keywords, consider using more efficient search logic.
                for keyword in rule["keywords"]:
                    if keyword.lower() not in content.lower():
                        return False
            except Exception as e:
                logger.error(f"Error checking keywords for {file_path}: {e}")
                return False

        return True

    async def sort_directory(self, directory: Path):
        """
        Sorts all files within a directory (recursively) according to the loaded rules.

        * If 'self.rules' is None, it calls 'load_rules' first.
        * For each file, it iterates through the rules. The first matching rule
          triggers the file to be moved to the specified 'target_dir'.

        Args:
            directory (Path): The directory to sort.
        """
        if self.rules is None:
            # ? Load the rules once if not already loaded.
            self.rules = await self.load_rules()

        # * Walk through each file in the directory tree.
        for file in directory.rglob("*"):
            if file.is_file():
                # ? Check each rule in turn until one matches.
                for rule in self.rules:
                    if await self.rule_matches_extended(file, rule):
                        target_dir = Path(rule.get("target_dir"))
                        if not target_dir.is_absolute():
                            target_dir = directory / target_dir

                        # ! Skip if the file is already in the target directory.
                        if file.parent == target_dir:
                            continue

                        await directory_manager.DirectoryManager.ensure_directory(
                            target_dir
                        )
                        logger.info(f"Applying rule {rule} to file {file}")
                        await file_mover.FileMover(directory).move_file(
                            file, target_dir / file.name
                        )
                        break  # * Stop after the first matching rule.

    def sort_directory_sync(self, directory: Path):
        """
        Synchronous wrapper around 'sort_directory' for convenience.

        * Uses 'asyncio.run' to execute the async method.

        Args:
            directory (Path): The directory to sort.
        """
        asyncio.run(self.sort_directory(directory))
