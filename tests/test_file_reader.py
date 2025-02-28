"""Tests for the file reader module."""

from pathlib import Path
from typing import List

import pytest

from aichemist_codex.file_reader import FileMetadata, FileReader


@pytest.fixture
def file_reader():
    """Create a FileReader instance for testing."""
    reader = FileReader(max_workers=2, preview_length=100)
    yield reader
    # Cleanup after tests
    reader.executor.shutdown(wait=False)


@pytest.fixture
def sample_text_file(tmp_path):
    """Create a sample text file for testing."""
    file_path = tmp_path / "sample.txt"
    file_path.write_text("This is a sample text file for testing.")
    return file_path


@pytest.fixture
def sample_binary_file(tmp_path):
    """Create a sample binary file for testing."""
    file_path = tmp_path / "sample.bin"
    file_path.write_bytes(b"\x00\x01\x02\x03")
    return file_path


@pytest.mark.asyncio
async def test_get_mime_type_text(file_reader, sample_text_file):
    """Test MIME type detection for text files."""
    mime_type = file_reader.get_mime_type(sample_text_file)
    assert mime_type.startswith("text/")


@pytest.mark.asyncio
async def test_get_mime_type_binary(file_reader, sample_binary_file):
    """Test MIME type detection for binary files."""
    mime_type = file_reader.get_mime_type(sample_binary_file)
    assert mime_type.startswith("application/")


@pytest.mark.asyncio
async def test_get_mime_type_nonexistent(file_reader, tmp_path):
    """Test MIME type detection for nonexistent files."""
    nonexistent_file = tmp_path / "nonexistent.txt"
    with pytest.raises(FileNotFoundError):
        file_reader.get_mime_type(nonexistent_file)


@pytest.mark.asyncio
async def test_get_mime_types_multiple(
    file_reader, sample_text_file, sample_binary_file
):
    """Test getting MIME types for multiple files."""
    mime_types = file_reader.get_mime_types([sample_text_file, sample_binary_file])
    assert len(mime_types) == 2
    assert mime_types[str(sample_text_file)].startswith("text/")
    assert mime_types[str(sample_binary_file)].startswith("application/")


@pytest.mark.asyncio
async def test_read_text_file(file_reader, sample_text_file):
    """Test reading a text file."""
    results = await file_reader.read_files([sample_text_file])
    assert len(results) == 1
    metadata = results[0]
    assert isinstance(metadata, FileMetadata)
    assert metadata.mime_type.startswith("text/")
    assert metadata.size > 0
    assert metadata.preview is not None
    assert len(metadata.preview) <= file_reader.preview_length + 3  # +3 for "..."


@pytest.mark.asyncio
async def test_read_binary_file(file_reader, sample_binary_file):
    """Test reading a binary file."""
    results = await file_reader.read_files([sample_binary_file])
    assert len(results) == 1
    metadata = results[0]
    assert isinstance(metadata, FileMetadata)
    assert metadata.mime_type.startswith("application/")
    assert metadata.size == 4  # We wrote 4 bytes
    assert metadata.preview == ""  # Binary files should have empty preview


@pytest.mark.asyncio
async def test_read_nonexistent_file(file_reader, tmp_path):
    """Test reading a file that doesn't exist."""
    nonexistent_file = tmp_path / "nonexistent.txt"
    results = await file_reader.read_files([nonexistent_file])
    assert len(results) == 1
    metadata = results[0]
    assert isinstance(metadata, FileMetadata)
    assert metadata.error is not None
    assert "cannot find the file" in metadata.error.lower()


@pytest.mark.asyncio
async def test_batch_file_reading(file_reader, tmp_path):
    """Test reading multiple files in batch."""
    # Create multiple test files
    files: List[Path] = []
    for i in range(3):
        file_path = tmp_path / f"test_{i}.txt"
        file_path.write_text(f"Content of file {i}")
        files.append(file_path)

    results = await file_reader.read_files(files)
    assert len(results) == 3

    for i, metadata in enumerate(results):
        assert isinstance(metadata, FileMetadata)
        assert metadata.mime_type.startswith("text/")
        assert metadata.size > 0
        assert metadata.preview is not None


@pytest.mark.asyncio
async def test_preview_length_limit(file_reader, tmp_path):
    """Test that file preview respects the length limit."""
    # Create a file with content longer than preview_length
    long_content = "x" * 200  # Longer than preview_length=100
    file_path = tmp_path / "long.txt"
    file_path.write_text(long_content)

    results = await file_reader.read_files([file_path])
    metadata = results[0]

    assert isinstance(metadata, FileMetadata)
    assert len(metadata.preview) <= file_reader.preview_length + 3  # +3 for "..."
    if len(long_content) > file_reader.preview_length:
        assert metadata.preview.endswith("...")
