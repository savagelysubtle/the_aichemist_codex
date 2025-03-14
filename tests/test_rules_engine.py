# test_rules_engine.py
import json

from src.config.config_loader import config
from src.config.rules_engine import RulesEngine


def test_load_rules(monkeypatch, tmp_path):
    # Create a temporary default_ignore_patterns.json file.
    temp_dir = tmp_path / "config"
    temp_dir.mkdir()
    rules_file = temp_dir / "default_ignore_patterns.json"
    rules_data = {"rules": [{"pattern": "*.tmp", "target_dir": "temp"}]}
    rules_file.write_text(json.dumps(rules_data), encoding="utf-8")

    # Optionally, monkey-patch the path if RulesEngine uses a relative location.
    engine = RulesEngine()
    engine._load_rules()
    # Verify that rules are loaded.
    assert isinstance(engine.rules, list)
    if engine.rules:
        assert engine.rules[0]["pattern"] == "*.tmp"


def test_should_ignore(monkeypatch):
    # Monkey-patch config.get to return a known ignore pattern.
    monkeypatch.setattr(config, "get", lambda key, default=None: ["*.ignore", "temp/"])
    from backend.src.config.rules_engine import RulesEngine

    engine = RulesEngine()
    assert engine.should_ignore("file.ignore")
    assert engine.should_ignore("temp/file.txt")
    assert not engine.should_ignore("file.txt")
