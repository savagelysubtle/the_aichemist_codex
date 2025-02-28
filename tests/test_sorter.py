from pathlib import Path

import pytest
import yaml

from aichemist_codex.file_manager.file_mover import FileMover
from aichemist_codex.file_manager.sorter import RuleBasedSorter


# Create a temporary config directory with a fake sorting_rules.yaml
@pytest.fixture
def temp_config_dir(tmp_path: Path) -> Path:
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    rules = {
        "rules": [{"pattern": "*.txt", "extensions": [".txt"], "target_dir": "sorted"}]
    }
    rules_file = config_dir / "sorting_rules.yaml"
    rules_file.write_text(yaml.dump(rules))
    return config_dir


# Override load_rules to load from our temporary config directory
class TestSorter(RuleBasedSorter):
    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
        self.rules = self.load_rules()

    def load_rules(self):
        rules_file = self.config_dir / "sorting_rules.yaml"
        if not rules_file.exists():
            return []
        try:
            with open(rules_file, "r", encoding="utf-8") as f:
                rules_data = yaml.safe_load(f)
            return rules_data.get("rules", [])
        except Exception:
            return []


@pytest.fixture
def sorter_with_temp_config(tmp_path: Path, temp_config_dir: Path) -> RuleBasedSorter:
    return TestSorter(temp_config_dir)


def test_rule_matches(sorter_with_temp_config: RuleBasedSorter, tmp_path: Path):
    dummy_file = tmp_path / "example.txt"
    dummy_file.write_text("dummy content")
    rule = {"pattern": "*.txt", "extensions": [".txt"], "target_dir": "sorted"}
    assert sorter_with_temp_config.rule_matches(dummy_file, rule)

    non_match_file = tmp_path / "example.md"
    non_match_file.write_text("dummy content")
    assert not sorter_with_temp_config.rule_matches(non_match_file, rule)


def test_sort_directory_moves_file(
    monkeypatch, sorter_with_temp_config: RuleBasedSorter, tmp_path: Path
):
    # Set up a temporary directory with a test file
    test_dir = tmp_path / "testdir"
    test_dir.mkdir()
    test_file = test_dir / "move_me.txt"
    test_file.write_text("move me")

    # Override FileMover.move_file to capture the move without doing actual OS moves
    moved_files = []

    def fake_move_file(source: Path, destination: Path):
        moved_files.append((source, destination))
        # simulate move: create destination and remove source
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(source.read_text())
        source.unlink()

    monkeypatch.setattr(FileMover, "move_file", staticmethod(fake_move_file))

    sorter_with_temp_config.sort_directory(test_dir)

    # Expect the file to have been moved into test_dir/sorted/
    target_file = test_dir / "sorted" / "move_me.txt"
    assert any(dest == target_file for _, dest in moved_files)
