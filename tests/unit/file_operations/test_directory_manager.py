import asyncio
import shutil
import tempfile
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest

from the_aichemist_codex.backend.file_manager.directory_manager import DirectoryManager


@pytest.fixture
def temp_dir() -> Generator[Path]:
    dir_path = tempfile.mkdtemp()
    yield Path(dir_path)
    shutil.rmtree(dir_path)


@pytest.fixture
def dir_manager_setup(
    temp_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, Path, Path, list[dict[str, str | None]]]:
    test_dir = Path(temp_dir) / "new_dir"
    rollback_log = Path(temp_dir) / "rollback.json"
    rollback_log.write_text("[]", encoding="utf-8")

    # Create a spy function to track calls
    recorded_operations: list[dict[str, str | None]] = []

    async def spy_record_operation(
        self: Any, operation: str, source: Path, destination: Path | None = None
    ) -> None:
        recorded_operations.append(
            {
                "operation": operation,
                "source": str(source),
                "destination": str(destination) if destination else None,
            }
        )

    # Patch the module's rollback_manager.record_operation
    import the_aichemist_codex.backend.rollback.rollback_manager

    monkeypatch.setattr(
        the_aichemist_codex.backend.rollback.rollback_manager.RollbackManager,
        "record_operation",
        spy_record_operation,
    )

    # Return the test dir, log, temp dir, and recorded operations for verification
    return test_dir, rollback_log, temp_dir, recorded_operations


@pytest.mark.file_operations
@pytest.mark.unit
def test_ensure_directory(
    dir_manager_setup: tuple[Path, Path, Path, list[dict[str, str | None]]],
) -> None:
    test_dir, _, _, recorded_operations = dir_manager_setup
    # Create a DirectoryManager instance
    dir_manager = DirectoryManager()
    # Initially, the directory should not exist.
    assert not test_dir.exists()  # noqa: S101
    # Create the directory asynchronously.
    asyncio.run(dir_manager.ensure_directory(test_dir))
    # Now the directory should exist.
    assert test_dir.exists()  # noqa: S101
    # Verify that a rollback operation was recorded with the correct source path
    assert len(recorded_operations) > 0  # noqa: S101
    assert any(
        op["operation"] == "create" and op["source"] == str(test_dir)
        for op in recorded_operations
    )  # noqa: S101


@pytest.mark.file_operations
@pytest.mark.unit
def test_cleanup_empty_dirs(
    dir_manager_setup: tuple[Path, Path, Path, list[dict[str, str | None]]],
) -> None:
    _, _, temp_dir, recorded_operations = dir_manager_setup
    empty_dir = Path(temp_dir) / "empty"
    empty_dir.mkdir()
    assert empty_dir.exists()  # noqa: S101
    # Create DirectoryManager instance
    dir_manager = DirectoryManager()
    # Run cleanup to remove empty directories asynchronously.
    asyncio.run(dir_manager.cleanup_empty_dirs(Path(temp_dir)))
    # The empty directory should be removed.
    assert not empty_dir.exists()  # noqa: S101
    # Verify that a delete operation was recorded
    assert len(recorded_operations) > 0  # noqa: S101
    assert any(
        op["operation"] == "delete" and op["source"] == str(empty_dir)
        for op in recorded_operations
    )  # noqa: S101
