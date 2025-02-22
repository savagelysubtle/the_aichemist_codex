"""Configuration system for project_reader similar to GitIngest."""

from pathlib import Path

import tomli

from .patterns import DEFAULT_IGNORE_PATTERNS


class CodexConfig:
    def __init__(self):
        self.max_file_size = 10 * 1024 * 1024  # 10 MB
        self.ignore_patterns = DEFAULT_IGNORE_PATTERNS

        config_file = Path(".codexconfig")
        if config_file.exists():
            try:
                with open(config_file, "rb") as f:
                    data = tomli.load(f)
                    self.__dict__.update(data.get("codex", {}))
            except Exception as e:
                print(f"Error loading config: {e}")
