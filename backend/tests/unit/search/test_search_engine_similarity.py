"""Tests for the similarity search methods in the SearchEngine class."""

import tempfile
from collections.abc import Generator
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from backend.src.search.search_engine import SearchEngine


@pytest.fixture
def temp_files() -> Generator[dict[str, Path | list[Path]]]:
    """Create temporary test files with content."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test files with different content
        file1 = Path(temp_dir) / "file1.txt"
        file1.write_text("This is a Python file about machine learning concepts.")

        file2 = Path(temp_dir) / "file2.txt"
        file2.write_text(
            "Machine learning and AI are fascinating topics in Python programming."
        )

        file3 = Path(temp_dir) / "file3.txt"
        file3.write_text("JavaScript is a programming language for web development.")

        yield {"dir": Path(temp_dir), "files": [file1, file2, file3]}


@pytest.fixture
def mock_similarity_provider() -> MagicMock:
    """Create a mock similarity provider for testing."""
    mock_provider = MagicMock()

    # Mock the search method
    async def mock_search(
        query: str,
        file_paths: list[Path] | None = None,
        threshold: float = 0.7,
        max_results: int = 10,
    ) -> list[str]:
        if "Python" in query:
            return ["file1.txt", "file2.txt"]
        elif "JavaScript" in query:
            return ["file3.txt"]
        else:
            return []

    # Mock the find_similar_files method
    async def mock_find_similar_files(
        file_path: Path,
        threshold: float = 0.7,
        max_results: int = 10,
    ) -> list[tuple[str, float]]:
        if "file1" in str(file_path) or "file2" in str(file_path):
            return [("file1.txt", 0.95), ("file2.txt", 0.85)]
        elif "file3" in str(file_path):
            return [("file3.txt", 1.0)]
        else:
            return []

    # Mock the find_file_groups method
    async def mock_find_file_groups(
        file_paths: list[Path] | None = None,
        threshold: float = 0.7,
        min_group_size: int = 2,
    ) -> list[list[str]]:
        return [["file1.txt", "file2.txt"], ["file3.txt"]]

    mock_provider.search = mock_search
    mock_provider.find_similar_files = mock_find_similar_files
    mock_provider.find_file_groups = mock_find_file_groups

    return mock_provider


@pytest.fixture
def mock_config() -> dict[str, bool | float | int]:
    """Create a mock configuration with similarity search enabled."""
    return {
        "enable_similarity_search": True,
        "SIMILARITY_THRESHOLD": 0.7,
        "SIMILARITY_MAX_RESULTS": 10,
        "SIMILARITY_MIN_GROUP_SIZE": 2,
    }


@pytest.fixture
def search_engine(
    mock_similarity_provider: MagicMock, mock_config: dict[str, bool | float | int]
) -> SearchEngine:
    """Create a SearchEngine instance with a mock similarity provider."""
    with patch("backend.search.search_engine.get_settings", return_value=mock_config):
        engine = SearchEngine(index_dir=Path("/test"))
        # Replace the similarity provider with our mock
        engine.similarity_provider = mock_similarity_provider
        return engine


class TestSearchEngineSimilarity:
    """Test cases for the similarity search methods in SearchEngine."""

    @pytest.mark.asyncio
    @pytest.mark.search
    @pytest.mark.unit
    async def test_find_similar_files_async(
        self, search_engine: SearchEngine, temp_files: dict[str, Path | list[Path]]
    ) -> None:
        """Test finding files similar to a specified file."""
        files = temp_files["files"]
        assert isinstance(files, list)  # noqa: S101
        file_path = files[0]

        # Test with a valid file
        results = await search_engine.find_similar_files_async(
            file_path=file_path, threshold=0.7, max_results=5
        )

        # Should have results
        assert len(results) > 0  # noqa: S101

        # Each result should be a dictionary with path and score
        for result in results:
            assert "path" in result  # noqa: S101
            assert "similarity_score" in result  # noqa: S101
            assert isinstance(result["path"], str)  # noqa: S101
            assert isinstance(result["similarity_score"], float)  # noqa: S101

    @pytest.mark.asyncio
    @pytest.mark.search
    @pytest.mark.unit
    async def test_find_similar_files_with_nonexistent_file(
        self, search_engine: SearchEngine
    ) -> None:
        """Test finding similar files with a nonexistent file path."""
        # Test with a nonexistent file
        with patch("os.path.exists", return_value=False):
            results = await search_engine.find_similar_files_async(
                file_path=Path("/nonexistent/file.txt")
            )

        # Should return an empty list
        assert results == []  # noqa: S101

    @pytest.mark.asyncio
    @pytest.mark.search
    @pytest.mark.unit
    async def test_find_similar_files_with_similarity_disabled(
        self, search_engine: SearchEngine
    ) -> None:
        """Test finding similar files with similarity search disabled."""
        # Modify the config to disable similarity search
        with patch(
            "backend.search.search_engine.get_settings",
            return_value={"enable_similarity_search": False},
        ):
            results = await search_engine.find_similar_files_async(
                file_path=Path("/test/file.txt")
            )

        # Should return an empty list
        assert results == []  # noqa: S101

    @pytest.mark.asyncio
    @pytest.mark.search
    @pytest.mark.unit
    async def test_find_file_groups_async(
        self, search_engine: SearchEngine, temp_files: dict[str, Path | list[Path]]
    ) -> None:
        """Test finding groups of similar files."""
        # Test with default parameters
        results = await search_engine.find_file_groups_async()

        # Should have results
        assert len(results) > 0  # noqa: S101

        # Each result should be a list of file paths
        for group in results:
            assert isinstance(group, list)  # noqa: S101
            assert all(isinstance(path, str) for path in group)  # noqa: S101

    @pytest.mark.asyncio
    @pytest.mark.search
    @pytest.mark.unit
    async def test_find_file_groups_with_specific_paths(
        self, search_engine: SearchEngine, temp_files: dict[str, Path | list[Path]]
    ) -> None:
        """Test finding groups of similar files with specific file paths."""
        # Test with specific file paths
        files = temp_files["files"]
        assert isinstance(files, list)  # noqa: S101

        results = await search_engine.find_file_groups_async(
            file_paths=[Path(str(f)) for f in files],
            threshold=0.8,
            min_group_size=2,
        )

        # Should have results
        assert len(results) > 0  # noqa: S101

        # Verify that search_provider.find_file_groups was
        # called with the right parameters
        assert search_engine.similarity_provider is not None  # noqa: S101
        search_engine.similarity_provider.find_file_groups.assert_called_with(
            file_paths=[str(f) for f in files],
            threshold=0.8,
            min_group_size=2,
        )

    @pytest.mark.asyncio
    @pytest.mark.search
    @pytest.mark.unit
    async def test_find_file_groups_with_similarity_disabled(
        self, search_engine: SearchEngine
    ) -> None:
        """Test finding file groups with similarity search disabled."""
        # Modify the config to disable similarity search
        with patch(
            "backend.search.search_engine.get_settings",
            return_value={"enable_similarity_search": False},
        ):
            results = await search_engine.find_file_groups_async()

        # Should return an empty list
        assert results == []  # noqa: S101
