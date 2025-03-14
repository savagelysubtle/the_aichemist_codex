# test_settings.py
from pathlib import Path

from backend.config.settings import (
    DEFAULT_IGNORE_PATTERNS,
    LOG_DIR,
    MAX_FILE_SIZE,
    MAX_TOKENS,
)


def test_default_settings():
    assert isinstance(DEFAULT_IGNORE_PATTERNS, list)
    assert MAX_FILE_SIZE > 0
    assert MAX_TOKENS > 0
    assert isinstance(LOG_DIR, Path)
