from pathlib import Path

import tomli


class CodexConfig:
    def __init__(self):
        self.settings = {
            "max_file_size": 10_000_000,
            "max_tokens": 8000,
            "ignore_patterns": set(),
        }

        config_file = Path(".codexconfig")
        if config_file.exists():
            self._load_config(config_file)

    def _load_config(self, path: Path):
        with open(path, "rb") as f:
            data = tomli.load(f)
            self.settings.update(data.get("codex", {}))
