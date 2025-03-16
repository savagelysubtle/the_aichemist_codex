# mypy: disable-error-code="attr-defined"
# mypy: ignore-errors
# ruff: noqa: F821, RUF009
import shutil
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from backend.src.file_reader.file_metadata import FileMetadata
from backend.src.search.providers.regex_provider import RegexSearchProvider
from backend.src.search.search_engine import SearchEngine  # type: ignore

# Test directories
TEST_INDEX_DIR = Path("test_search_index")
TEST_DB_PATH = Path("test_search_index.sqlite")


@pytest.fixture(scope="function")
def setup_search_engine(tmp_path: Path) -> SearchEngine:
    """Fixture to set up the SearchEngine with a temporary directory."""
    index_dir = tmp_path / "index"
    index_dir.mkdir()
    db_path = tmp_path / "search_index.sqlite"
    search_engine = SearchEngine(index_dir=index_dir, db_path=db_path)
    return search_engine


@pytest.fixture
def sample_files(tmp_path: Path) -> list[FileMetadata]:
    """Fixture to create sample files in a temporary directory for testing."""
    test_dir = tmp_path / "test_files"
    test_dir.mkdir()

    files = [
        test_dir / "example1.txt",
        test_dir / "example2.txt",
        test_dir / "photo1.jpg",
    ]

    # ✅ Ensure text files contain searchable content
    files[0].write_text("This is a test file for full-text search indexing.")
    files[1].write_text("Another document with some searchable content.")
    files[2].write_bytes(b"\xff\xd8\xff")  # Simulating a JPG file

    return [
        FileMetadata(
            path=files[0],
            mime_type="text/plain",
            size=files[0].stat().st_size,
            extension=".txt",
            preview="This is a test file.",
        ),
        FileMetadata(
            path=files[1],
            mime_type="text/plain",
            size=files[1].stat().st_size,
            extension=".txt",
            preview="Another document.",
        ),
        FileMetadata(
            path=files[2],
            mime_type="image/jpeg",
            size=files[2].stat().st_size,
            extension=".jpg",
            preview="",
        ),
    ]


def wait_for_indexing() -> None:
    """Pause execution to allow Whoosh & SQLite to process new entries."""
    time.sleep(0.2)


def test_add_to_index(
    setup_search_engine: SearchEngine, sample_files: list[FileMetadata]
) -> None:
    """Test adding files to the search index and metadata storage."""
    search_engine = setup_search_engine

    for file_metadata in sample_files:
        search_engine.add_to_index(file_metadata)  # type: ignore

    # Verify that the files were indexed
    results = search_engine.search_filename("example1")  # type: ignore

    # Normalize paths for comparison
    expected_path = str(sample_files[0].path.resolve())
    normalized_results = [str(Path(result).resolve()) for result in results]

    assert expected_path in normalized_results, (  # noqa: S101
        f"{expected_path} should be in the search results."
    )


def test_filename_search(
    setup_search_engine: SearchEngine, sample_files: list[FileMetadata]
) -> None:
    """Test searching for filenames."""
    search_engine = setup_search_engine

    for file_metadata in sample_files:
        search_engine.add_to_index(file_metadata)  # type: ignore

    results = search_engine.search_filename("example1")  # type: ignore
    assert len(results) == 1, "Filename search should return exactly one result."  # noqa: S101


def test_fuzzy_search(
    setup_search_engine: SearchEngine, sample_files: list[FileMetadata]
) -> None:
    """Test fuzzy search functionality."""
    search_engine = setup_search_engine

    for file_metadata in sample_files:
        search_engine.add_to_index(file_metadata)  # type: ignore

    wait_for_indexing()  # ✅ Let SQLite process data

    results = search_engine.fuzzy_search("exmple")  # type: ignore

    # ✅ Debugging Output
    print(f"Indexed files: {sample_files}")
    print(f"Fuzzy search results: {results}")

    assert len(results) >= 1, "Fuzzy search should find example1.txt"  # noqa: S101


def test_full_text_search(
    setup_search_engine: SearchEngine, sample_files: list[FileMetadata]
) -> None:
    """Test full-text search on indexed file content."""
    search_engine = setup_search_engine

    for file_metadata in sample_files:
        search_engine.add_to_index(file_metadata)  # type: ignore

    wait_for_indexing()  # ✅ Give Whoosh time to process

    results = search_engine.full_text_search("searchable")  # type: ignore
    assert len(results) >= 1, "Full-text search should return at least one result."  # noqa: S101
    assert any("example2.txt" in path for path in results), (  # noqa: S101
        "example2.txt should be found."
    )


def test_metadata_search(
    setup_search_engine: SearchEngine, sample_files: list[FileMetadata]
) -> None:
    """Test searching files by metadata filters."""
    search_engine = setup_search_engine

    for file_metadata in sample_files:
        search_engine.add_to_index(file_metadata)  # type: ignore

    wait_for_indexing()  # ✅ Allow SQLite to update

    results = search_engine.metadata_search(  # type: ignore
        {
            "extension": [".txt"],
            "size_min": 10,
            "size_max": 5000,
        }  # ✅ Adjust size range
    )

    # ✅ Debugging Output
    print(f"Indexed files: {[f.path for f in sample_files]}")
    print(f"Metadata search results: {results}")

    # Normalize expected paths
    expected_path = str(sample_files[0].path.resolve())
    normalized_results = [str(Path(result).resolve()) for result in results]

    assert len(results) == 1, f"Expected 1 match, got {len(results)}"  # noqa: S101
    assert expected_path in normalized_results, (  # noqa: S101
        f"{expected_path} should match search criteria."
    )


def test_empty_search_results(setup_search_engine: SearchEngine) -> None:
    """Test searches when no files have been indexed."""
    search_engine = setup_search_engine

    assert search_engine.search_filename("nonexistent") == []  # type: ignore # noqa: S101
    assert search_engine.fuzzy_search("unknown") == []  # type: ignore # noqa: S101
    assert search_engine.full_text_search("nothing") == []  # type: ignore # noqa: S101
    assert search_engine.metadata_search({"extension": [".docx"]}) == []  # type: ignore # noqa: S101


def test_error_handling_in_indexing(setup_search_engine: SearchEngine) -> None:
    """Test error handling when adding a non-existent file to the index."""
    search_engine = setup_search_engine

    non_existent_file = FileMetadata(
        path=Path("/invalid/path.txt"),
        mime_type="text/plain",
        size=1234,
        extension=".txt",
        preview="This file does not exist.",
    )

    search_engine.add_to_index(non_existent_file)  # type: ignore
    results = search_engine.search_filename("path.txt")  # type: ignore
    assert len(results) == 0, "Non-existent files should not be indexed."  # noqa: S101


def test_sqlite_indexing_speed(
    setup_search_engine: SearchEngine, tmp_path: Path
) -> None:
    """Ensure SQLite indexing improves search speed."""
    search_engine = setup_search_engine

    # Insert 5000 sample files
    for i in range(5000):
        file_path = tmp_path / f"file_{i}.txt"
        file_path.write_text(f"Content {i}")

        file_metadata = FileMetadata(
            path=file_path,
            mime_type="text/plain",
            size=file_path.stat().st_size,
            extension=".txt",
            preview=f"Content {i}",
        )
        search_engine.add_to_index(file_metadata)  # type: ignore

    # Perform a filename search
    import time

    start_time = time.time()
    results = search_engine.search_filename("file_4999")  # type: ignore
    end_time = time.time()

    assert len(results) == 1, "Filename search should return exactly one result."  # noqa: S101
    assert end_time - start_time < 0.5, (  # noqa: S101
        "Search should be optimized and return results quickly."
    )


def test_whoosh_recovery_on_corruption(setup_search_engine: SearchEngine) -> None:
    """Test handling of Whoosh index corruption."""
    search_engine = setup_search_engine

    # Corrupt the index by deleting files
    shutil.rmtree(search_engine.index_dir)

    # Reinitialize search engine (should recover automatically)
    search_engine._initialize_index()

    assert search_engine.index is not None, (  # noqa: S101
        "Search engine should recover from index corruption."
    )


@pytest.mark.asyncio
async def test_regex_search(
    self: object, search_engine: SearchEngine, temp_dir: Path
) -> None:
    """Test regex search functionality."""
    # Create test files with regex patterns
    file1 = temp_dir / "regex_test1.txt"
    file1.write_text("This file contains a pattern: ABC-123-XYZ")

    file2 = temp_dir / "regex_test2.txt"
    file2.write_text("Another file with pattern: DEF-456-UVW")

    file3 = temp_dir / "regex_test3.txt"
    file3.write_text("This file has no pattern")

    # Index the files
    await search_engine.add_to_index_async(
        FileMetadata(
            path=file1,
            mime_type="text/plain",
            size=100,
            extension=".txt",
            preview=file1.read_text(),
        )
    )
    await search_engine.add_to_index_async(
        FileMetadata(
            path=file2,
            mime_type="text/plain",
            size=100,
            extension=".txt",
            preview=file2.read_text(),
        )
    )
    await search_engine.add_to_index_async(
        FileMetadata(
            path=file3,
            mime_type="text/plain",
            size=100,
            extension=".txt",
            preview=file3.read_text(),
        )
    )

    # Enable regex search provider
    # Set up the regex provider directly
    search_engine.regex_provider = RegexSearchProvider()

    # Test regex search
    results = await search_engine.regex_search_async(r"[A-Z]{3}-\d{3}-[A-Z]{3}")
    assert len(results) == 2  # noqa: S101
    assert str(file1) in results  # noqa: S101
    assert str(file2) in results  # noqa: S101
    assert str(file3) not in results  # noqa: S101

    # Test case sensitive search
    file4 = temp_dir / "regex_test4.txt"
    file4.write_text("This file has lowercase pattern: abc-123-xyz")
    await search_engine.add_to_index_async(
        FileMetadata(
            path=file4,
            mime_type="text/plain",
            size=100,
            extension=".txt",
            preview=file4.read_text(),
        )
    )

    results = await search_engine.regex_search_async(
        r"[A-Z]{3}-\d{3}-[A-Z]{3}", case_sensitive=True
    )
    assert len(results) == 2  # noqa: S101
    assert str(file4) not in results  # noqa: S101

    # Test with case insensitive
    results = await search_engine.regex_search_async(
        r"[A-Z]{3}-\d{3}-[A-Z]{3}", case_sensitive=False
    )
    assert len(results) == 3  # noqa: S101
    assert str(file4) in results  # noqa: S101


@pytest.mark.asyncio
async def test_search_method_dispatch(
    self: object, search_engine: SearchEngine, temp_dir: Path
) -> None:
    """Test that the search method correctly dispatches to different search types."""
    # Create test files
    file1 = temp_dir / "dispatch_test1.txt"
    file1.write_text("This is a test file for dispatch testing")

    file2 = temp_dir / "dispatch_test2.txt"
    file2.write_text("Another file with different content")

    # Index the files
    await search_engine.add_to_index_async(
        FileMetadata(
            path=file1,
            mime_type="text/plain",
            size=100,
            extension=".txt",
            preview=file1.read_text(),
        )
    )
    await search_engine.add_to_index_async(
        FileMetadata(
            path=file2,
            mime_type="text/plain",
            size=100,
            extension=".txt",
            preview=file2.read_text(),
        )
    )

    # Test filename search
    with patch.object(search_engine, "search_filename_async") as mock_filename_search:
        mock_filename_search.return_value = [str(file1)]
        results = search_engine.search("dispatch_test1", method="filename")
        mock_filename_search.assert_called_once_with("dispatch_test1")
        assert len(results) == 1  # noqa: S101
        assert results[0]["path"] == str(file1)  # noqa: S101

    # Test fuzzy search
    with patch.object(search_engine, "fuzzy_search_async") as mock_fuzzy_search:
        mock_fuzzy_search.return_value = [str(file2)]
        results = search_engine.search("dispatch", method="fuzzy")
        mock_fuzzy_search.assert_called_once_with("dispatch")
        assert len(results) == 1  # noqa: S101
        assert results[0]["path"] == str(file2)  # noqa: S101

    # Test fulltext search
    with patch.object(search_engine, "full_text_search") as mock_fulltext_search:
        mock_fulltext_search.return_value = [str(file1), str(file2)]
        results = search_engine.search("test", method="fulltext")
        mock_fulltext_search.assert_called_once_with("test")
        assert len(results) == 2  # noqa: S101
