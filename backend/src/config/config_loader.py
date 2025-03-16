"""Handles loading of project configuration settings."""

import logging
from pathlib import Path

import tomli

CONFIG_FILE = Path(__file__).resolve().parent / ".codexconfig"


class CodexConfig:
    """Loads configuration settings for The Aichemist Codex."""

    def __init__(self):
        """Initialize with default settings."""
        # ✅ Delay import to avoid circular import issues
        from .settings import DEFAULT_IGNORE_PATTERNS, MAX_FILE_SIZE, MAX_TOKENS

        self.settings = {
            "ignore_patterns": DEFAULT_IGNORE_PATTERNS,
            "max_file_size": MAX_FILE_SIZE,
            "max_tokens": MAX_TOKENS,
        }
        self._load_config_file()

    def _load_config_file(self):
        """Loads user-defined settings from `.codexconfig`."""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "rb") as f:
                    user_config = tomli.load(f).get("codex", {})
                    self.settings.update(user_config)
            except Exception as e:
                logging.error(f"Error loading config: {e}")

    def get(self, key, default=None):
        """Retrieve a configuration setting."""
        return self.settings.get(key, default)


# ✅ Singleton instance to use across the project
config = CodexConfig()
