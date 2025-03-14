import json
import time
import tempfile
import shutil
import pytest
from pathlib import Path

from backend.rollback.rollback_manager import RollbackManager, RollbackOperation

@pytest.fixture
def rollback_manager_setup():
    temp_dir = tempfile.mkdtemp()
    rollback_log_path = Path(temp_dir) / "rollback.json"
    rollback_log_path.write_text("[]", encoding="utf-8")
    manager = RollbackManager(rollback_log=rollback_log_path)
    yield manager, rollback_log_path, temp_dir
    shutil.rmtree(temp_dir)

def test_record_operation(rollback_manager_setup):
    manager, rollback_log_path, _ = rollback_manager_setup
    manager.record_operation("move", "/tmp/src.txt", "/tmp/dest.txt")
    data = json.loads(rollback_log_path.read_text(encoding="utf-8"))
    assert any(op.get("operation") == "move" for op in data)

def test_undo_and_redo_move(rollback_manager_setup):
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
    assert dest_file.exists()
    assert not src_file.exists()

    # Undo: should move the file back.
    result = manager.undo_last_operation()
    assert result
    assert src_file.exists()
    assert not dest_file.exists()

    # Redo: should move it again.
    result_redo = manager.redo_last_undone()
    assert result_redo
    assert not src_file.exists()
    assert dest_file.exists()

def test_cleanup_old_entries(rollback_manager_setup):
    manager, rollback_log_path, _ = rollback_manager_setup
    old_timestamp = time.time() - (10 * 86400)
    new_timestamp = time.time()
    data = [
        {"timestamp": old_timestamp, "operation": "move", "source": "/old/src", "destination": "/old/dest"},
        {"timestamp": new_timestamp, "operation": "move", "source": "/new/src", "destination": "/new/dest"}
    ]
    rollback_log_path.write_text(json.dumps(data), encoding="utf-8")
    manager.cleanup_old_entries(retention_days=7)
    cleaned_data = json.loads(rollback_log_path.read_text(encoding="utf-8"))
    assert len(cleaned_data) == 1
    assert cleaned_data[0]["source"] == "/new/src"
