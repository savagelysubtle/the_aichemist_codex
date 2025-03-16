# test_aggregator.py
from pathlib import Path

from backend.src.ingest.aggregator import aggregate_digest


def test_aggregate_digest(tmp_path: Path) -> None:
    # Create dummy files.
    file1 = tmp_path / "file1.txt"
    file2 = tmp_path / "file2.txt"
    file1.write_text("Content 1", encoding="utf-8")
    file2.write_text("Content 2", encoding="utf-8")

    # Create a content map.
    content_map = {
        file1: file1.read_text(encoding="utf-8"),
        file2: file2.read_text(encoding="utf-8"),
    }

    digest = aggregate_digest([file1, file2], content_map)
    assert "Total Files:" in digest  # noqa: S101
    assert "file1.txt" in digest  # noqa: S101
    assert "file2.txt" in digest  # noqa: S101
