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

    (source / "file1.txt").write_text(
        "Text file"
    )  # ✅ Ensures the file exists before deleting it
    return source, target  # ✅ Returns both directories


def test_missing_file_handling(setup_test_dirs, caplog):
    """Test missing file handling and ensure logging works."""
    source, target = setup_test_dirs

    # ✅ Simulate a missing file
    missing_file = source / "file1.txt"
    assert missing_file.exists(), "❌ file1.txt was never created!"
    missing_file.unlink()

    rules = [{"target_dir": str(target), "extensions": [".txt"]}]

    # ✅ Ensure logger is properly configured
    logger = logging.getLogger("file_manager.rules_engine")
    logger.setLevel(logging.DEBUG)

    # ✅ Capture logs correctly
    with caplog.at_level(logging.DEBUG, logger="file_manager.rules_engine"):
        apply_rules(str(source), rules)

    # ✅ Verify logs
    assert any(
        "file not found" in record.message.lower() for record in caplog.records
    ), "❌ Log message not found!"
