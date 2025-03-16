# test_settings.py
from pathlib import Path

from backend.src.config.settings import (
    DEFAULT_IGNORE_PATTERNS,
    LOG_DIR,
    MAX_FILE_SIZE,
    MAX_TOKENS,
)


def test_default_settings() -> None:
    assert isinstance(DEFAULT_IGNORE_PATTERNS, list)  # noqa: S101
    assert MAX_FILE_SIZE > 0  # noqa: S101
    assert MAX_TOKENS > 0  # noqa: S101
    assert isinstance(LOG_DIR, Path)  # noqa: S101
