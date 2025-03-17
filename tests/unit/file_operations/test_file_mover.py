import asyncio
import shutil
import tempfile
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest
from pytest import MonkeyPatch

from the_aichemist_codex.backend.file_manager.file_mover import FileMover


@pytest.fixture
def file_mover_setup(
    monkeypatch: MonkeyPatch,
) -> Generator[tuple[FileMover, Path, Path, list[dict[str, str | None]], Path]]:
    temp_dir = tempfile.mkdtemp()
    base_dir = Path(temp_dir)
    test_file = base_dir / "test.txt"
    test_file.write_text("file content", encoding="utf-8")
    destination_file = base_dir / "dest" / "test.txt"

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

    mover = FileMover(base_dir)
    yield (
        mover,
        test_file,
        destination_file,
        recorded_operations,
        Path(temp_dir),
    )
    shutil.rmtree(temp_dir)


@pytest.mark.file_operations
@pytest.mark.unit
def test_move_file(
    file_mover_setup: tuple[FileMover, Path, Path, list[dict[str, str | None]], Path],
) -> None:
    mover, test_file, destination_file, recorded_operations, _ = file_mover_setup
    # Use the static move_file method (which is what our code is using now)
    asyncio.run(FileMover.move_file(test_file, destination_file))
    # Check that the destination file exists and the source file has been removed.
    assert destination_file.exists()  # noqa: S101
    assert not test_file.exists()  # noqa: S101
    # Verify that a move operation was recorded
    assert len(recorded_operations) > 0  # noqa: S101
    assert any(
        op["operation"] == "move"
        and op["source"] == str(test_file)
        and op["destination"] == str(destination_file)
        for op in recorded_operations
    )  # noqa: S101
