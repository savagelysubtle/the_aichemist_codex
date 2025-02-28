"""Script to test if SafeFileHandler correctly excludes ignored files."""

import logging
from pathlib import Path

from aichemist_codex.utils.safety import SafeFileHandler

logger = logging.getLogger(__name__)

# Define test paths
test_paths = [
    Path("/path/to/project/.venv/main.py"),
    Path("/path/to/project/src/main.py"),
    Path("/path/to/project/node_modules/test.js"),
    Path("/path/to/project/tests/test_main.py"),
]

# Check ignored files
for test_path in test_paths:
    if SafeFileHandler.should_ignore(test_path):
        logger.info(f"✅ Correctly ignored: {test_path}")
    else:
        logger.warning(f"⚠️ NOT ignored: {test_path}")
