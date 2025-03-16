import pytest
# test_file_metadata.py
from pathlib import Path

from backend.src.file_reader.file_metadata import FileMetadata


@pytest.mark.[a-z]+

@pytest.mark.unit
def test_file_metadata_instantiation() -> None:
    meta = FileMetadata(
        path=Path("test.txt"),
        mime_type="text/plain",
        size=100,
        extension=".txt",
        preview="This is a test preview",
    )
    assert meta.path == Path("test.txt")  # noqa: S101
    assert meta.mime_type == "text/plain"  # noqa: S101
    assert meta.size == 100  # noqa: S101
    assert meta.extension == ".txt"  # noqa: S101
    assert meta.preview == "This is a test preview"  # noqa: S101
