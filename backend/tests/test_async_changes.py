import asyncio
import tempfile
from pathlib import Path

import pytest
import yaml

from backend.src.file_manager.directory_manager import DirectoryManager
from backend.src.file_manager.duplicate_detector import DuplicateDetector
from backend.src.file_manager.file_mover import FileMover
from backend.src.file_manager.file_tree import generate_file_tree  # now async
from backend.src.file_manager.sorter import RuleBasedSorter
from backend.src.file_reader.file_reader import FileReader
from backend.src.file_reader.parsers import JsonParser, TextParser

# Import updated modules (adjust paths as needed)
from backend.src.utils import AsyncFileIO


# --- Helper for YAML reading ---
async def read_yaml(path: Path):
    content = await AsyncFileIO.read(path)
    return yaml.safe_load(content)


# --- Async I/O Tests ---


@pytest.mark.asyncio
async def test_async_read_write():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        test_file = tmp_path / "test.txt"
        content = "Hello, async world!"
        write_success = await AsyncFileIO.write(test_file, content)
        assert write_success, "Failed to write file asynchronously."
        read_content = await AsyncFileIO.read(test_file)
        assert read_content == content, "Read content does not match written content."


@pytest.mark.asyncio
async def test_json_parser():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        test_file = tmp_path / "test.json"
        data = {"key": "value", "num": 42}
        write_success = await AsyncFileIO.write_json(test_file, data)
        assert write_success, "Failed to write JSON file asynchronously."

        parser = JsonParser()
        parsed_data = await parser.parse(test_file)
        assert (
            parsed_data["content"] == data
        ), "Parsed JSON does not match original data."
        preview = parser.get_preview(parsed_data)
        assert "key" in preview, "Preview does not contain expected content."


@pytest.mark.asyncio
async def test_text_parser():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        test_file = tmp_path / "test.txt"
        content = "Line1\nLine2\nLine3"
        await AsyncFileIO.write(test_file, content)
        parser = TextParser()
        parsed_data = await parser.parse(test_file)
        preview = parser.get_preview(parsed_data, max_length=10)
        assert preview.endswith("..."), "Text preview did not truncate as expected."


@pytest.mark.asyncio
async def test_file_reader_process_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        test_file = tmp_path / "sample.txt"
        sample_content = "This is a sample file content for testing."
        await AsyncFileIO.write(test_file, sample_content)
        # Set preview_length=20 so preview becomes first 20 chars + "..."
        file_reader = FileReader(preview_length=20)
        metadata = await file_reader.process_file(test_file)
        # Since 20 characters of sample_content is "This is a sample fil"
        expected_preview_start = "This is a sample fil"
        assert metadata.preview.startswith(
            expected_preview_start
        ), f"FileReader preview incorrect. Expected to start with '{expected_preview_start}' but got '{metadata.preview}'"
        # MIME type should be detected as text
        assert metadata.mime_type.startswith("text/"), "MIME type not detected as text."


@pytest.mark.asyncio
async def test_directory_manager():
    with tempfile.TemporaryDirectory() as tmpdir:
        new_dir = Path(tmpdir) / "new_directory"
        await DirectoryManager.ensure_directory(new_dir)
        assert (
            new_dir.exists() and new_dir.is_dir()
        ), "Directory was not created asynchronously."


@pytest.mark.asyncio
async def test_duplicate_detector(tmp_path_factory):
    tmp_dir = tmp_path_factory.mktemp("duplicates")
    file1 = tmp_dir / "file1.txt"
    file2 = tmp_dir / "file2.txt"
    content = "duplicate content"
    await AsyncFileIO.write(file1, content)
    await AsyncFileIO.write(file2, content)
    detector = DuplicateDetector()
    await detector.scan_directory(tmp_dir)
    duplicates = detector.get_duplicates()
    assert any(
        len(files) > 1 for files in duplicates.values()
    ), "No duplicates detected when expected."


@pytest.mark.asyncio
async def test_file_mover(tmp_path_factory):
    tmp_dir = tmp_path_factory.mktemp("mover")
    source_file = tmp_dir / "source.txt"
    dest_dir = tmp_dir / "dest"
    content = "move me"
    await AsyncFileIO.write(source_file, content)
    mover = FileMover(tmp_dir)
    await mover.move_file(source_file, dest_dir / source_file.name)
    assert not source_file.exists(), "Source file still exists after moving."
    assert (
        dest_dir / source_file.name
    ).exists(), "Destination file not found after moving."


@pytest.mark.asyncio
async def test_file_tree_generation(tmp_path_factory):
    tmp_dir = tmp_path_factory.mktemp("file_tree")
    (tmp_dir / "file1.txt").write_text("content1", encoding="utf-8")
    subdir = tmp_dir / "subdir"
    subdir.mkdir()
    (subdir / "file2.txt").write_text("content2", encoding="utf-8")
    output_file = tmp_dir / "file_tree.json"
    # Now call the async version
    await generate_file_tree(tmp_dir, output_file)
    file_tree = await AsyncFileIO.read_json(output_file)
    assert "file1.txt" in file_tree, "file1.txt not found in generated file tree."
    assert "subdir" in file_tree, "subdir not found in generated file tree."


@pytest.mark.asyncio
async def test_sorter(tmp_path_factory, monkeypatch):
    tmp_dir = tmp_path_factory.mktemp("sorter")
    file_to_sort = tmp_dir / "sort_me.txt"
    await AsyncFileIO.write(file_to_sort, "content for sorting")
    config_dir = tmp_dir / "config"
    config_dir.mkdir()
    rules_file = config_dir / "sorting_rules.yaml"
    rules_data = {
        "rules": [
            {"pattern": "sort_me.txt", "extensions": [".txt"], "target_dir": "sorted"}
        ]
    }
    await AsyncFileIO.write(rules_file, yaml.dump(rules_data))

    async def load_rules_override(self):
        data = await read_yaml(rules_file)
        return data.get("rules", [])

    monkeypatch.setattr(RuleBasedSorter, "load_rules", load_rules_override)

    sorter = RuleBasedSorter()
    await sorter.sort_directory(tmp_dir)
    # Increase delay to 1 second for all async operations to complete.
    await asyncio.sleep(1.0)
    assert not file_to_sort.exists(), "File was not moved by sorter."
    sorted_file = tmp_dir / "sorted" / "sort_me.txt"
    # Check asynchronously that the destination file exists.
    assert await AsyncFileIO.exists(
        sorted_file
    ), "Sorted file not found in target directory."
