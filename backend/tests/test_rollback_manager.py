import json
import shutil
import tempfile
import time
from collections.abc import Generator
from pathlib import Path

import pytest

from backend.src.rollback.rollback_manager import RollbackManager, RollbackOperation


@pytest.fixture
def rollback_manager_setup() -> Generator[tuple[RollbackManager, Path, str]]:
    temp_dir = tempfile.mkdtemp()
    rollback_log_path = Path(temp_dir) / "rollback.json"
    rollback_log_path.write_text("[]", encoding="utf-8")
    manager = RollbackManager(rollback_log=rollback_log_path)
    yield manager, rollback_log_path, temp_dir
    shutil.rmtree(temp_dir)


@pytest.mark.asyncio
async def test_record_operation(
    rollback_manager_setup: tuple[RollbackManager, Path, str],
) -> None:
    manager, rollback_log_path, temp_dir = rollback_manager_setup
    src_path = Path(temp_dir) / "src.txt"
    dest_path = Path(temp_dir) / "dest.txt"
    await manager.record_operation("move", str(src_path), str(dest_path))
    data = json.loads(rollback_log_path.read_text(encoding="utf-8"))
    assert any(op.get("operation") == "move" for op in data)  # noqa: S101


@pytest.mark.asyncio
async def test_undo_and_redo_move(
    rollback_manager_setup: tuple[RollbackManager, Path, str],
) -> None:
    manager, _, temp_dir = rollback_manager_setup
    src_file = Path(temp_dir) / "test.txt"
    dest_file = Path(temp_dir) / "moved.txt"
    src_file.write_text("content", encoding="utf-8")

    # Manually record a move operation.
    op = RollbackOperation("move", str(src_file), str(dest_file))
    manager._undo_stack.append(op)

    # Simulate the move operation by actually moving the file.
    import shutil

    shutil.move(str(src_file), str(dest_file))
    assert dest_file.exists()  # noqa: S101
    assert not src_file.exists()  # noqa: S101

    # Undo: should move the file back.
    result = await manager.undo_last_operation()
    assert result  # noqa: S101
    assert src_file.exists()  # noqa: S101
    assert not dest_file.exists()  # noqa: S101

    # Redo: should move it again.
    result_redo = await manager.redo_last_undone()
    assert result_redo  # noqa: S101
    assert not src_file.exists()  # noqa: S101
    assert dest_file.exists()  # noqa: S101


@pytest.mark.asyncio
async def test_cleanup_old_entries(
    rollback_manager_setup: tuple[RollbackManager, Path, str],
) -> None:
    manager, rollback_log_path, _ = rollback_manager_setup
    old_timestamp = time.time() - (10 * 86400)
    new_timestamp = time.time()
    data = [
        {
            "timestamp": old_timestamp,
            "operation": "move",
            "source": "/old/src",
            "destination": "/old/dest",
        },
        {
            "timestamp": new_timestamp,
            "operation": "move",
            "source": "/new/src",
            "destination": "/new/dest",
        },
    ]
    rollback_log_path.write_text(json.dumps(data), encoding="utf-8")
    await manager.cleanup_old_entries(retention_days=7)
    cleaned_data = json.loads(rollback_log_path.read_text(encoding="utf-8"))
    assert len(cleaned_data) == 1  # noqa: S101
    assert cleaned_data[0]["source"] == "/new/src"  # noqa: S101
