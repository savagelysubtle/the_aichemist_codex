import logging

import pytest

from file_manager.rules_engine import apply_rules


@pytest.fixture
def setup_test_dirs(tmp_path):
    """Set up a source directory with test files and a target directory."""
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()

    (source / "file1.txt").write_text("Text file")
    (source / "file2.log").write_text("Log file")

    return source, target


def test_missing_file_handling(setup_test_dirs, caplog):
    """Test that missing files do not cause crashes."""
    source, target = setup_test_dirs

    # Simulate a missing file
    (source / "file1.txt").unlink()

    # Explicitly capture logging
    logger = logging.getLogger()
    logger.setLevel(logging.WARNING)

    with caplog.at_level(logging.WARNING):
        rules = [{"target_dir": str(target), "extensions": [".txt"]}]
        apply_rules(str(source), rules)

    assert any("File not found" in message for message in caplog.messages)
