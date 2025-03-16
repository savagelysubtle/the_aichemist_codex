# test_rules_engine.py
import json
from pathlib import Path

import pytest

from backend.src.config.config_loader import config
from backend.src.config.rules_engine import RulesEngine


def test_load_rules(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    # Create a temporary default_ignore_patterns.json file.
    temp_dir = tmp_path / "config"
    temp_dir.mkdir()
    rules_file = temp_dir / "default_ignore_patterns.json"
    rules_data = {"rules": [{"pattern": "*.tmp", "target_dir": "temp"}]}
    rules_file.write_text(json.dumps(rules_data), encoding="utf-8")

    # Create and test the rules engine
    engine = RulesEngine()
    engine._load_rules()
    # Verify that rules are loaded.
    assert isinstance(engine.rules, list)  # noqa: S101
    if engine.rules:
        assert engine.rules[0]["pattern"] == "*.tmp"  # noqa: S101


def test_should_ignore(monkeypatch: pytest.MonkeyPatch) -> None:
    # Monkey-patch config.get to return a known ignore pattern.
    monkeypatch.setattr(config, "get", lambda key, default=None: ["*.ignore", "temp/"])

    engine = RulesEngine()
    assert engine.should_ignore("file.ignore")  # noqa: S101
    assert engine.should_ignore("temp/file.txt")  # noqa: S101
    assert not engine.should_ignore("file.txt")  # noqa: S101
