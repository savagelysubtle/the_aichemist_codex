"""Handles file organization rules for The Aichemist Codex."""

import json
import logging
from pathlib import Path

from .config_loader import config

logger = logging.getLogger(__name__)


class RulesEngine:
    """Manages dynamic file movement rules."""

    def __init__(self):
        self.rules = []
        self._load_rules()

    def _load_rules(self):
        """Loads file handling rules from a configuration file."""
        rules_file = Path(__file__).resolve().parent / "default_ignore_patterns.json"
        if rules_file.exists():
            try:
                with open(rules_file, "r", encoding="utf-8") as f:
                    self.rules = json.load(f).get("rules", [])
            except Exception as e:
                logger.error(f"Failed to load rules: {e}")

    def should_ignore(self, file_path: str) -> bool:
        """Checks if a file should be ignored based on defined patterns."""
        ignore_patterns = config.get("ignore_patterns")
        return any(file_path.endswith(pattern) for pattern in ignore_patterns)


rules_engine = RulesEngine()
