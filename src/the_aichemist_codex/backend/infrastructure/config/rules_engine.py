"""
Rules engine for file organization and processing rules.

This module provides functionality for defining and evaluating
rules based on configuration settings.
"""

import json
import logging
import re
from pathlib import Path
from re import Pattern
from typing import Any

from ...core.exceptions import ConfigError
from ...registry import Registry

logger = logging.getLogger(__name__)


class Rule:
    """
    Represents a processing rule for files.

    This class encapsulates the logic for evaluating whether a file
    matches specific criteria defined in a rule.
    """

    def __init__(
        self,
        name: str,
        pattern: str = None,
        extensions: list[str] = None,
        target_dir: str = None,
        description: str = None,
        preserve_path: bool = False,
        criteria: dict[str, Any] = None,
    ):
        """
        Initialize a rule.

        Args:
            name: Name of the rule
            pattern: Optional regex pattern to match file paths
            extensions: Optional list of file extensions to match
            target_dir: Optional target directory for matched files
            description: Optional description of the rule
            preserve_path: Whether to preserve directory structure
            criteria: Optional additional criteria for matching
        """
        self.name = name
        self.pattern = pattern
        self.extensions = [ext.lower() for ext in extensions] if extensions else []
        self.target_dir = target_dir
        self.description = description
        self.preserve_path = preserve_path
        self.criteria = criteria or {}

        # Compile regex pattern if provided
        self._compiled_pattern: Pattern = None
        if pattern:
            try:
                self._compiled_pattern = re.compile(pattern)
            except re.error as e:
                logger.error(f"Invalid regex pattern in rule '{name}': {e}")
                self._compiled_pattern = None

    def matches(self, file_path: Path) -> bool:
        """
        Check if a file matches this rule.

        Args:
            file_path: Path to the file to check

        Returns:
            True if the file matches the rule, False otherwise
        """
        # Check file extension
        if (
            self.extensions
            and file_path.suffix.lower().lstrip(".") not in self.extensions
        ):
            return False

        # Check regex pattern
        if self._compiled_pattern and not self._compiled_pattern.search(str(file_path)):
            return False

        # Additional criteria could be implemented here

        return True

    def apply(self, file_path: Path) -> Path:
        """
        Apply the rule to a file path.

        Args:
            file_path: Path to the file

        Returns:
            New path for the file according to the rule

        Raises:
            ValueError: If target_dir is not set
        """
        if not self.target_dir:
            raise ValueError(f"Rule '{self.name}' does not define a target directory")

        target = Path(self.target_dir)

        if self.preserve_path:
            # Preserve the directory structure
            relative_path = file_path.relative_to(file_path.anchor)
            return target / relative_path
        else:
            # Just use the filename
            return target / file_path.name

    @classmethod
    def from_dict(cls, rule_dict: dict[str, Any]) -> "Rule":
        """
        Create a Rule from a dictionary.

        Args:
            rule_dict: Dictionary containing rule definition

        Returns:
            Initialized Rule object
        """
        return cls(
            name=rule_dict.get("name", "Unnamed Rule"),
            pattern=rule_dict.get("pattern"),
            extensions=rule_dict.get("extensions"),
            target_dir=rule_dict.get("target_dir"),
            description=rule_dict.get("description"),
            preserve_path=rule_dict.get("preserve_path", False),
            criteria=rule_dict.get("criteria"),
        )


class RulesEngine:
    """
    Engine for managing and applying file processing rules.

    This class provides functionality for loading, managing, and
    evaluating rules for file organization and processing.
    """

    def __init__(self):
        """
        Initialize the rules engine.

        Loads rules from the configuration.
        """
        self._registry = Registry.get_instance()
        self._config = self._registry.config_provider
        self._rules: list[Rule] = []
        self._load_rules()

    def _load_rules(self) -> None:
        """
        Load rules from configuration.

        This method loads rules from the configuration and from
        a rules file if specified in the configuration.
        """
        try:
            # Load rules from configuration
            rules_config = self._config.get_config("rules", [])

            if isinstance(rules_config, list):
                for rule_dict in rules_config:
                    self._rules.append(Rule.from_dict(rule_dict))

            # Load rules from file if specified
            rules_file = self._config.get_config("rules_file")
            if rules_file:
                self._load_rules_from_file(rules_file)

            logger.info(f"Loaded {len(self._rules)} rules")
        except Exception as e:
            logger.error(f"Error loading rules: {e}")

    def _load_rules_from_file(self, file_path: str) -> None:
        """
        Load rules from a file.

        Args:
            file_path: Path to the rules file

        Raises:
            ConfigError: If the file cannot be loaded
        """
        try:
            path_obj = Path(file_path)
            if not path_obj.exists():
                logger.warning(f"Rules file not found: {file_path}")
                return

            with open(path_obj) as f:
                if path_obj.suffix.lower() == ".json":
                    rules_data = json.load(f)
                elif path_obj.suffix.lower() in [".yaml", ".yml"]:
                    import yaml

                    rules_data = yaml.safe_load(f)
                else:
                    raise ConfigError(
                        f"Unsupported rules file format: {path_obj.suffix}"
                    )

            if "rules" in rules_data and isinstance(rules_data["rules"], list):
                for rule_dict in rules_data["rules"]:
                    self._rules.append(Rule.from_dict(rule_dict))
            else:
                logger.warning(f"No 'rules' list found in rules file: {file_path}")

        except Exception as e:
            logger.error(f"Error loading rules from file {file_path}: {e}")
            raise ConfigError(f"Failed to load rules from file: {e}")

    def get_rules(self) -> list[Rule]:
        """
        Get all loaded rules.

        Returns:
            List of Rule objects
        """
        return self._rules.copy()

    def add_rule(self, rule: Rule) -> None:
        """
        Add a rule to the engine.

        Args:
            rule: Rule to add
        """
        self._rules.append(rule)

    def find_matching_rules(self, file_path: Path) -> list[Rule]:
        """
        Find all rules that match a file.

        Args:
            file_path: Path to the file

        Returns:
            List of matching Rule objects
        """
        return [rule for rule in self._rules if rule.matches(file_path)]

    def should_ignore(self, file_path: str) -> bool:
        """
        Check if a file should be ignored based on ignore patterns.

        Args:
            file_path: Path to the file

        Returns:
            True if the file should be ignored, False otherwise
        """
        ignore_patterns = self._config.get_config("ignore_patterns", [])

        if not ignore_patterns:
            return False

        path_str = str(file_path)
        return any(
            re.search(pattern, path_str) for pattern in ignore_patterns if pattern
        )
