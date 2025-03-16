# tests/test_ingest.py

from pathlib import Path

from backend.src.ingest import generate_digest


def test_generate_digest_with_empty_dir(tmp_path: Path) -> None:
    # Create a temporary directory (this is automatically provided by
    # pytest's tmp_path fixture)
    # It will be empty so we can check that our function handles it gracefully.
    digest = generate_digest(
        tmp_path, options={"include_patterns": {"*"}, "ignore_patterns": set()}
    )
    # For an empty directory, we expect the digest to at least contain the summary.
    assert "Total Files:" in digest  # noqa: S101
