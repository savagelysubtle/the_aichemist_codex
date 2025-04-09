"""Handles file organization rules for The Aichemist Codex."""

import logging

logger = logging.getLogger(__name__)


class RulesEngine:
    """Manages dynamic file movement rules."""

    def __init__(self) -> None:
        self.rules = []
        self._load_rules()

    def _load_rules(self) -> None:
        """Loads file handling rules from a configuration file."""
        # For now, use default rules to avoid config dependency
        self.rules = []

        # Default ignore patterns
        self._ignore_patterns = [
            ".git",
            "__pycache__",
            ".venv",
            ".env",
            "node_modules",
            ".DS_Store",
            "*.pyc",
            "*.pyo",
            "*.pyd",
            ".pytest_cache",
            ".coverage",
            "htmlcov",
            ".idea",
            ".vscode",
            "*.swp",
            "*.swo",
        ]

    def should_ignore(self, file_path: str) -> bool:
        """Checks if a file should be ignored based on defined patterns."""
        # Simple pattern matching for now
        for pattern in self._ignore_patterns:
            if pattern.startswith("*"):
                if file_path.endswith(pattern[1:]):
                    return True
            else:
                if pattern in file_path:
                    return True
        return False


rules_engine = RulesEngine()
