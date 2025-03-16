import logging
from pathlib import Path

import pytest

from backend.src.config.logging_config import setup_logging


def test_logging_setup(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    # Override the log directory with a temporary directory.
    temp_log_dir = tmp_path / "logs"
    temp_log_dir.mkdir()
    monkeypatch.setattr("backend.config.logging_config.LOG_DIR", temp_log_dir)
    log_file = temp_log_dir / "project.log"
    if log_file.exists():
        log_file.unlink()
    setup_logging()

    logger = logging.getLogger("test_logging")
    logger.info("Test message")

    # Check that the log file exists and contains the test message.
    assert log_file.exists()  # noqa: S101
    content = log_file.read_text(encoding="utf-8")
    assert "Test message" in content  # noqa: S101
