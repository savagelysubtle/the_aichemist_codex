import time
from pathlib import Path

from aichemist_codex.file_manager.file_mover import FileMover
from aichemist_codex.file_manager.file_watcher import FileEventHandler


# Dummy event class to simulate watchdog events.
class DummyEvent:
    def __init__(self, src_path: str, is_directory: bool = False):
        self.src_path = src_path
        self.is_directory = is_directory


def test_file_watcher_debounce(monkeypatch, tmp_path: Path):
    # Create a temporary directory to watch.
    watch_dir = tmp_path / "watch"
    watch_dir.mkdir()
    test_file = watch_dir / "testfile.txt"
    test_file.write_text("content")

    base_directory = watch_dir
    handler = FileEventHandler(base_directory)

    # Override move_file to capture moves.
    moved_files = []

    def fake_move_file(source: Path, destination: Path):
        moved_files.append((source, destination))
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(source.read_text())
        source.unlink()

    monkeypatch.setattr(FileMover, "move_file", staticmethod(fake_move_file))

    # Simulate a file creation event.
    event = DummyEvent(str(test_file), is_directory=False)
    handler.on_created(event)

    # Wait for the debounce timer to expire.
    time.sleep(handler.debounce_interval + 1)

    # Verify that one move occurred.
    assert len(moved_files) == 1
    _, destination = moved_files[0]
    assert destination.name == "testfile.txt"
    assert "organized" in str(destination)


def test_file_watcher_multiple_events(monkeypatch, tmp_path: Path):
    # Create a temporary directory and file.
    watch_dir = tmp_path / "watch_multi"
    watch_dir.mkdir()
    test_file = watch_dir / "multi.txt"
    test_file.write_text("content")

    base_directory = watch_dir
    handler = FileEventHandler(base_directory)

    call_count = 0

    def fake_move_file(source: Path, destination: Path):
        nonlocal call_count
        call_count += 1
        source.unlink()

    monkeypatch.setattr(FileMover, "move_file", staticmethod(fake_move_file))

    event = DummyEvent(str(test_file), is_directory=False)
    # Simulate multiple rapid events.
    handler.on_created(event)
    handler.on_created(event)
    handler.on_created(event)

    time.sleep(handler.debounce_interval + 1)
    # Expect that only one move occurred due to debouncing.
    assert call_count == 1
