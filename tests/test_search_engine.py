import shutil
import time
from pathlib import Path

import pytest

from backend.file_reader.file_metadata import FileMetadata
from backend.search.search_engine import SearchEngine

# Test directories
TEST_INDEX_DIR = Path("test_search_index")
TEST_DB_PATH = Path("test_search_index.sqlite")


@pytest.fixture(scope="function")
def setup_search_engine(tmp_path):
    """Fixture to set up the SearchEngine with a temporary directory."""
    index_dir = tmp_path / "index"
    index_dir.mkdir()
    db_path = tmp_path / "search_index.sqlite"
    search_engine = SearchEngine(index_dir=index_dir, db_path=db_path)
    return search_engine


@pytest.fixture
def sample_files(tmp_path):
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
    files[2].write_bytes(b"\xFF\xD8\xFF")  # Simulating a JPG file

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


def wait_for_indexing():
    """Pause execution to allow Whoosh & SQLite to process new entries."""
    time.sleep(0.2)


def test_add_to_index(setup_search_engine, sample_files):
    """Test adding files to the search index and metadata storage."""
    search_engine = setup_search_engine

    for file_metadata in sample_files:
        search_engine.add_to_index(file_metadata)

    # Verify that the files were indexed
    results = search_engine.search_filename("example1")

    # Normalize paths for comparison
    expected_path = str(sample_files[0].path.resolve())
    normalized_results = [str(Path(result).resolve()) for result in results]

    assert (
        expected_path in normalized_results
    ), f"{expected_path} should be in the search results."


def test_filename_search(setup_search_engine, sample_files):
    """Test searching for filenames."""
    search_engine = setup_search_engine

    for file_metadata in sample_files:
        search_engine.add_to_index(file_metadata)

    results = search_engine.search_filename("example1")
    assert len(results) == 1, "Filename search should return exactly one result."


def test_fuzzy_search(setup_search_engine, sample_files):
    """Test fuzzy search functionality."""
    search_engine = setup_search_engine

    for file_metadata in sample_files:
        search_engine.add_to_index(file_metadata)

    wait_for_indexing()  # ✅ Let SQLite process data

    results = search_engine.fuzzy_search("exmple")

    # ✅ Debugging Output
    print(f"Indexed files: {sample_files}")
    print(f"Fuzzy search results: {results}")

    assert len(results) >= 1, "Fuzzy search should find example1.txt"


def test_full_text_search(setup_search_engine, sample_files):
    """Test full-text search on indexed file content."""
    search_engine = setup_search_engine

    for file_metadata in sample_files:
        search_engine.add_to_index(file_metadata)

    wait_for_indexing()  # ✅ Give Whoosh time to process

    results = search_engine.full_text_search("searchable")
    assert len(results) >= 1, "Full-text search should return at least one result."
    assert any(
        "example2.txt" in path for path in results
    ), "example2.txt should be found."


def test_metadata_search(setup_search_engine, sample_files):
    """Test searching files by metadata filters."""
    search_engine = setup_search_engine

    for file_metadata in sample_files:
        search_engine.add_to_index(file_metadata)

    wait_for_indexing()  # ✅ Allow SQLite to update

    results = search_engine.metadata_search(
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

    assert len(results) == 1, f"Expected 1 match, got {len(results)}"
    assert (
        expected_path in normalized_results
    ), f"{expected_path} should match search criteria."


def test_empty_search_results(setup_search_engine):
    """Test searches when no files have been indexed."""
    search_engine = setup_search_engine

    assert search_engine.search_filename("nonexistent") == []
    assert search_engine.fuzzy_search("unknown") == []
    assert search_engine.full_text_search("nothing") == []
    assert search_engine.metadata_search({"extension": [".docx"]}) == []


def test_error_handling_in_indexing(setup_search_engine):
    """Test error handling when adding a non-existent file to the index."""
    search_engine = setup_search_engine

    non_existent_file = FileMetadata(
        path=Path("/invalid/path.txt"),
        mime_type="text/plain",
        size=1234,
        extension=".txt",
        preview="This file does not exist.",
    )

    search_engine.add_to_index(non_existent_file)
    results = search_engine.search_filename("path.txt")
    assert len(results) == 0, "Non-existent files should not be indexed."


def test_sqlite_indexing_speed(setup_search_engine, tmp_path):
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
        search_engine.add_to_index(file_metadata)

    # Perform a filename search
    import time

    start_time = time.time()
    results = search_engine.search_filename("file_4999")
    end_time = time.time()

    assert len(results) == 1, "Filename search should return exactly one result."
    assert (
        end_time - start_time < 0.5
    ), "Search should be optimized and return results quickly."


def test_whoosh_recovery_on_corruption(setup_search_engine):
    """Test handling of Whoosh index corruption."""
    search_engine = setup_search_engine

    # Corrupt the index by deleting files
    shutil.rmtree(search_engine.index_dir)

    # Reinitialize search engine (should recover automatically)
    search_engine._initialize_index()

    assert (
        search_engine.index is not None
    ), "Search engine should recover from index corruption."
