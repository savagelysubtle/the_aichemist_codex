# test_file_metadata.py
from pathlib import Path

from backend.file_reader.file_metadata import FileMetadata


def test_file_metadata_instantiation():
    meta = FileMetadata(
        path=Path("test.txt"),
        mime_type="text/plain",
        size=100,
        extension=".txt",
        preview="This is a test preview",
    )
    assert meta.path == Path("test.txt")
    assert meta.mime_type == "text/plain"
    assert meta.size == 100
    assert meta.extension == ".txt"
    assert meta.preview == "This is a test preview"
