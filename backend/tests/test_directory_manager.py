import os
import tempfile
import shutil
import asyncio
import json
import pytest
from pathlib import Path

from src.file_manager import directory_manager
from src.rollback.rollback_manager import RollbackManager

@pytest.fixture
def temp_dir():
    dir_path = tempfile.mkdtemp()
    yield dir_path
    shutil.rmtree(dir_path)

@pytest.fixture
def dir_manager_setup(temp_dir):
    test_dir = Path(temp_dir) / "new_dir"
    rollback_log = Path(temp_dir) / "rollback.json"
    rollback_log.write_text("[]", encoding="utf-8")
    # Patch the module’s rollback_manager
    directory_manager.rollback_manager = RollbackManager(rollback_log=rollback_log)
    return test_dir, rollback_log, temp_dir

def test_ensure_directory(dir_manager_setup):
    test_dir, rollback_log, _ = dir_manager_setup
    # Initially, the directory should not exist.
    assert not test_dir.exists()
    # Create the directory asynchronously.
    asyncio.run(directory_manager.DirectoryManager.ensure_directory(test_dir))
    # Now the directory should exist.
    assert test_dir.exists()
    # Verify that a "create" rollback operation was recorded.
    data = json.loads(rollback_log.read_text(encoding="utf-8"))
    assert any(op.get("operation") == "create" for op in data)

def test_cleanup_empty_dirs(dir_manager_setup):
    _, _, temp_dir = dir_manager_setup
    empty_dir = Path(temp_dir) / "empty"
    empty_dir.mkdir()
    assert empty_dir.exists()
    # Run cleanup to remove empty directories asynchronously.
    asyncio.run(directory_manager.DirectoryManager.cleanup_empty_dirs(Path(temp_dir)))
    # The empty directory should be removed.
    assert not empty_dir.exists()
