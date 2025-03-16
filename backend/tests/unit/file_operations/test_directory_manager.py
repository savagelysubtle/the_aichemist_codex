import asyncio
import json
import shutil
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest

from backend.src.file_manager.directory_manager import DirectoryManager
from backend.src.rollback.rollback_manager import RollbackManager


@pytest.fixture
def temp_dir() -> Generator[Path]:
    dir_path = tempfile.mkdtemp()
    yield Path(dir_path)
    shutil.rmtree(dir_path)


@pytest.fixture
def dir_manager_setup(
    temp_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, Path, Path]:
    test_dir = Path(temp_dir) / "new_dir"
    rollback_log = Path(temp_dir) / "rollback.json"
    rollback_log.write_text("[]", encoding="utf-8")
    # Patch the module's rollback_manager
    monkeypatch.setattr(
        DirectoryManager, "rollback_manager", RollbackManager(rollback_log=rollback_log)
    )
    return test_dir, rollback_log, temp_dir


@pytest.mark.[a-z]+

@pytest.mark.unit
def test_ensure_directory(dir_manager_setup: tuple[Path, Path, Path]) -> None:
    test_dir, rollback_log, _ = dir_manager_setup
    # Initially, the directory should not exist.
    assert not test_dir.exists()  # noqa: S101
    # Create the directory asynchronously.
    asyncio.run(DirectoryManager.ensure_directory(test_dir))
    # Now the directory should exist.
    assert test_dir.exists()  # noqa: S101
    # Verify that a "create" rollback operation was recorded.
    data = json.loads(rollback_log.read_text(encoding="utf-8"))
    assert any(op.get("operation") == "create" for op in data)  # noqa: S101


@pytest.mark.[a-z]+

@pytest.mark.unit
def test_cleanup_empty_dirs(dir_manager_setup: tuple[Path, Path, Path]) -> None:
    _, _, temp_dir = dir_manager_setup
    empty_dir = Path(temp_dir) / "empty"
    empty_dir.mkdir()
    assert empty_dir.exists()  # noqa: S101
    # Run cleanup to remove empty directories asynchronously.
    asyncio.run(DirectoryManager.cleanup_empty_dirs(Path(temp_dir)))
    # The empty directory should be removed.
    assert not empty_dir.exists()  # noqa: S101
