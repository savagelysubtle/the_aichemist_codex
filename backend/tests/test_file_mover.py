import tempfile
import shutil
import asyncio
import json
import pytest
from pathlib import Path

from src.file_manager import file_mover
from src.rollback.rollback_manager import RollbackManager

@pytest.fixture
def file_mover_setup():
    temp_dir = tempfile.mkdtemp()
    base_dir = Path(temp_dir)
    test_file = base_dir / "test.txt"
    test_file.write_text("file content", encoding="utf-8")
    destination_file = base_dir / "dest" / "test.txt"
    rollback_log = Path(temp_dir) / "rollback.json"
    rollback_log.write_text("[]", encoding="utf-8")
    # Patch the FileMover's rollback_manager with our test rollback log.
    file_mover.rollback_manager = RollbackManager(rollback_log=rollback_log)
    mover = file_mover.FileMover(base_dir)
    yield mover, test_file, destination_file, rollback_log, temp_dir
    shutil.rmtree(temp_dir)

def test_move_file(file_mover_setup):
    mover, test_file, destination_file, rollback_log, _ = file_mover_setup
    asyncio.run(file_mover.FileMover.move_file(test_file, destination_file))
    # Check that the destination file exists and the source file has been removed.
    assert destination_file.exists()
    assert not test_file.exists()
    # Verify that a "move" operation was recorded in the rollback log.
    data = json.loads(rollback_log.read_text(encoding="utf-8"))
    assert any(op.get("operation") == "move" for op in data)
