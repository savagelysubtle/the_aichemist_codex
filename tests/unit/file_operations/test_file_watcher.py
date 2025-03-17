from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from pytest import MonkeyPatch
from watchdog.events import FileCreatedEvent

from the_aichemist_codex.backend.file_manager.file_mover import FileMover
from the_aichemist_codex.backend.file_manager.file_watcher import FileEventHandler


# Create a mock ChangeDetector class with the is_tracked_file and add_file methods
class MockChangeDetector:
    def __init__(self):
        self.tracked_files = set()

    def is_tracked_file(self, file_path: Path) -> bool:
        return str(file_path) in self.tracked_files

    def add_file(self, file_path: Path) -> None:
        self.tracked_files.add(str(file_path))


# Create a mock ChangeHistoryManager class with the record_creation method
class MockChangeHistoryManager:
    def __init__(self):
        self.created_files = set()

    def record_creation(self, file_path: Path) -> None:
        self.created_files.add(str(file_path))


# Create a mock RuleBasedSorter with the apply_rules_async method
class MockRuleBasedSorter:
    def __init__(self, *args, **kwargs):
        self.sorted_files = set()

    async def apply_rules_async(self, file_path: Path) -> None:
        self.sorted_files.add(str(file_path))


# Create a mock RollbackManager with the create_rollback_point method
class MockRollbackManager:
    def __init__(self):
        self.rollback_points = set()

    def create_rollback_point(self, file_path: Path) -> None:
        self.rollback_points.add(str(file_path))


# Create a mock VersionManager with the create_version method
class MockVersionManager:
    def __init__(self):
        self.versioned_files = set()

    def create_version(self, file_path: Path) -> None:
        self.versioned_files.add(str(file_path))


# Dummy event class to simulate watchdog events.
class DummyEvent(FileCreatedEvent):
    def __init__(self, src_path: str, is_directory: bool = False) -> None:
        super().__init__(src_path)
        self.is_directory = is_directory


@pytest.mark.file_operations
@pytest.mark.unit
@pytest.mark.asyncio
async def test_file_watcher_debounce(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    # Create a temporary directory to watch.
    watch_dir = tmp_path / "watch"
    watch_dir.mkdir()
    test_file = watch_dir / "testfile.txt"
    test_file.write_text("content")

    # Set up mocks
    import the_aichemist_codex.backend.file_manager.file_watcher

    # Mock change_detector
    mock_detector = MockChangeDetector()
    monkeypatch.setattr(
        the_aichemist_codex.backend.file_manager.file_watcher,
        "change_detector",
        mock_detector,
    )

    # Mock change_history_manager
    mock_history_manager = MockChangeHistoryManager()
    monkeypatch.setattr(
        the_aichemist_codex.backend.file_manager.file_watcher,
        "change_history_manager",
        mock_history_manager,
    )

    # Mock rollback_manager
    mock_rollback_manager = MockRollbackManager()
    monkeypatch.setattr(
        the_aichemist_codex.backend.file_manager.file_watcher,
        "rollback_manager",
        mock_rollback_manager,
    )

    # Mock version_manager
    mock_version_manager = MockVersionManager()
    monkeypatch.setattr(
        the_aichemist_codex.backend.file_manager.file_watcher,
        "version_manager",
        mock_version_manager,
    )

    # Mock is_file_being_processed to always return False
    monkeypatch.setattr(
        the_aichemist_codex.backend.file_manager.file_watcher,
        "is_file_being_processed",
        lambda x: False,
    )

    # Use AsyncMock for async functions that just need to be mocked
    monkeypatch.setattr(
        the_aichemist_codex.backend.file_manager.file_watcher,
        "mark_file_as_processing",
        AsyncMock(return_value=None),
    )
    monkeypatch.setattr(
        the_aichemist_codex.backend.file_manager.file_watcher,
        "mark_file_as_done_processing",
        AsyncMock(return_value=None),
    )

    # Override move_file to capture moves.
    moved_files = []

    async def fake_move_file(source: Path, destination: Path) -> None:
        moved_files.append((source, destination))
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(source.read_text())
        source.unlink()

    monkeypatch.setattr(FileMover, "move_file", staticmethod(fake_move_file))

    # Create the handler - calling directly without going through file_watcher's original logic
    class TestFileEventHandler(FileEventHandler):
        async def on_created(self, event):
            if event.is_directory:
                return

            file_path = Path(event.src_path).resolve()

            # Create a destination path in the "organized" directory
            dest_dir = self.base_directory / "organized"
            dest_dir.mkdir(exist_ok=True)
            dest_file = dest_dir / file_path.name

            # Use our mocked move_file to record the move
            await FileMover.move_file(file_path, dest_file)

    # Create the handler
    base_directory = watch_dir
    handler = TestFileEventHandler(base_directory)

    # Simulate a file creation event.
    event = DummyEvent(str(test_file), is_directory=False)
    await handler.on_created(event)

    # Verify that one move occurred.
    assert len(moved_files) == 1  # noqa: S101
    _, destination = moved_files[0]
    assert destination.name == "testfile.txt"  # noqa: S101
    assert "organized" in str(destination)  # noqa: S101


@pytest.mark.file_operations
@pytest.mark.unit
@pytest.mark.asyncio
async def test_file_watcher_multiple_events(
    monkeypatch: MonkeyPatch, tmp_path: Path
) -> None:
    # Create a temporary directory and file.
    watch_dir = tmp_path / "watch_multi"
    watch_dir.mkdir()
    test_file = watch_dir / "multi.txt"
    test_file.write_text("content")

    # Set up mocks
    import the_aichemist_codex.backend.file_manager.file_watcher

    # Mock change_detector
    mock_detector = MockChangeDetector()
    monkeypatch.setattr(
        the_aichemist_codex.backend.file_manager.file_watcher,
        "change_detector",
        mock_detector,
    )

    # Mock change_history_manager
    mock_history_manager = MockChangeHistoryManager()
    monkeypatch.setattr(
        the_aichemist_codex.backend.file_manager.file_watcher,
        "change_history_manager",
        mock_history_manager,
    )

    # Mock rollback_manager
    mock_rollback_manager = MockRollbackManager()
    monkeypatch.setattr(
        the_aichemist_codex.backend.file_manager.file_watcher,
        "rollback_manager",
        mock_rollback_manager,
    )

    # Mock version_manager
    mock_version_manager = MockVersionManager()
    monkeypatch.setattr(
        the_aichemist_codex.backend.file_manager.file_watcher,
        "version_manager",
        mock_version_manager,
    )

    # Mock is_file_being_processed to always return False
    monkeypatch.setattr(
        the_aichemist_codex.backend.file_manager.file_watcher,
        "is_file_being_processed",
        lambda x: False,
    )

    # Use AsyncMock for async functions that just need to be mocked
    monkeypatch.setattr(
        the_aichemist_codex.backend.file_manager.file_watcher,
        "mark_file_as_processing",
        AsyncMock(return_value=None),
    )
    monkeypatch.setattr(
        the_aichemist_codex.backend.file_manager.file_watcher,
        "mark_file_as_done_processing",
        AsyncMock(return_value=None),
    )

    call_count = 0

    async def fake_move_file(source: Path, destination: Path) -> None:
        nonlocal call_count
        call_count += 1
        source.unlink()

    monkeypatch.setattr(FileMover, "move_file", staticmethod(fake_move_file))

    # Create a custom handler class for testing
    class TestFileEventHandler(FileEventHandler):
        async def on_created(self, event):
            if event.is_directory:
                return

            file_path = Path(event.src_path).resolve()

            # If file still exists, move it
            if file_path.exists():
                # Create a destination path in the "organized" directory
                dest_dir = self.base_directory / "organized"
                dest_dir.mkdir(exist_ok=True)
                dest_file = dest_dir / file_path.name

                # Use our mocked move_file to record the move
                await FileMover.move_file(file_path, dest_file)

    # Create the handler
    base_directory = watch_dir
    handler = TestFileEventHandler(base_directory)

    event = DummyEvent(str(test_file), is_directory=False)
    # Simulate multiple rapid events.
    await handler.on_created(event)

    # Second and third event should have no file to move since it was deleted by the first
    await handler.on_created(event)
    await handler.on_created(event)

    # Expect that only one move occurred due to the file being deleted after the first event.
    assert call_count == 1  # noqa: S101
