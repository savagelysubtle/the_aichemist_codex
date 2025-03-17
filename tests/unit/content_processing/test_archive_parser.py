import zipfile
from pathlib import Path

import pytest

from the_aichemist_codex.backend.file_reader.parsers import ArchiveParser


@pytest.fixture
def sample_zip(tmp_path: Path) -> Path:
    """Create a temporary ZIP archive with two text files."""
    zip_path = tmp_path / "test.zip"
    # Create two dummy files
    file1 = tmp_path / "file1.txt"
    file1.write_text("Hello, world!")
    file2 = tmp_path / "file2.txt"
    file2.write_text("Another file")
    # Create a ZIP archive including them
    with zipfile.ZipFile(zip_path, "w") as zipf:
        zipf.write(file1, arcname="file1.txt")
        zipf.write(file2, arcname="file2.txt")
    return zip_path


@pytest.mark.asyncio
@pytest.mark.content_processing
@pytest.mark.unit
async def test_archive_parser_zip(sample_zip: Path) -> None:
    """Test ArchiveParser on a ZIP archive."""
    parser = ArchiveParser()
    result = await parser.parse(sample_zip)
    assert "files" in result  # noqa: S101
    assert "count" in result  # noqa: S101
    assert "file1.txt" in result["files"]  # noqa: S101
    assert "file2.txt" in result["files"]  # noqa: S101
    assert result["count"] == 2  # noqa: S101


@pytest.mark.asyncio
@pytest.mark.content_processing
@pytest.mark.unit
async def test_archive_parser_unsupported(tmp_path: Path) -> None:
    """Test ArchiveParser raises ValueError for an unsupported format."""
    dummy_file = tmp_path / "dummy.rar"
    dummy_file.write_text("dummy content")
    parser = ArchiveParser()
    with pytest.raises(ValueError):
        await parser.parse(dummy_file)
