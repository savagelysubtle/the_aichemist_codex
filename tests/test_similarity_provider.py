"""Tests for the similarity-based search provider."""

import asyncio
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from backend.search.providers.similarity_provider import SimilarityProvider


@pytest.fixture
def temp_files():
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

        file4 = Path(temp_dir) / "file4.txt"
        file4.write_text(
            "Python is great for data science, machine learning, and AI applications."
        )

        file5 = Path(temp_dir) / "file5.txt"
        file5.write_text("Web development often uses JavaScript, HTML, and CSS.")

        yield {"dir": Path(temp_dir), "files": [file1, file2, file3, file4, file5]}


@pytest.fixture
def mock_embedding_model():
    """Create a mock embedding model for testing."""
    mock_model = MagicMock()

    # Define embeddings for different content types
    python_ml_embedding = np.array([0.1, 0.8, 0.1], dtype="float32")
    javascript_web_embedding = np.array([0.8, 0.1, 0.1], dtype="float32")

    # Map specific content to expected embeddings
    def mock_encode(text):
        if "Python" in text and "machine learning" in text:
            return python_ml_embedding
        elif "JavaScript" in text and "web" in text:
            return javascript_web_embedding
        elif "Python" in text:
            return np.array([0.2, 0.7, 0.1], dtype="float32")
        elif "JavaScript" in text:
            return np.array([0.7, 0.2, 0.1], dtype="float32")
        else:
            return np.array([0.33, 0.33, 0.33], dtype="float32")

    mock_model.encode = mock_encode
    return mock_model


@pytest.fixture
def mock_faiss_index():
    """Create a mock FAISS index for testing."""
    mock_index = MagicMock()

    # Define the search method to return indices and distances
    def mock_search(query_vector, k):
        # Always return the first k indices with distance 0.1
        indices = np.array([[i for i in range(min(k, 5))]])
        distances = np.array([[0.1 * (i + 1) for i in range(min(k, 5))]])
        return distances, indices

    mock_index.search = mock_search
    return mock_index


@pytest.fixture
def similarity_provider(mock_embedding_model, mock_faiss_index):
    """Create a SimilarityProvider instance with mock components."""
    path_mapping = [str(Path(f"file{i}.txt")) for i in range(1, 6)]

    mock_cache = MagicMock()
    mock_cache.get.return_value = None  # No cache hits by default

    provider = SimilarityProvider(
        embedding_model=mock_embedding_model,
        vector_index=mock_faiss_index,
        path_mapping=path_mapping,
        cache_manager=mock_cache,
    )

    return provider


class TestSimilarityProvider:
    """Test cases for the SimilarityProvider class."""

    @pytest.mark.asyncio
    async def test_search_with_text_query(self, similarity_provider):
        """Test searching for files similar to a text query."""
        # Search for Python and machine learning related files
        results = await similarity_provider.search(
            query="Python machine learning concepts", threshold=0.5, max_results=3
        )

        # Should return results since we have files about Python and machine learning
        assert len(results) > 0

        # The paths should be strings from the path_mapping
        for path in results:
            assert isinstance(path, str)
            assert path.startswith("file")

    @pytest.mark.asyncio
    async def test_find_similar_files(self, similarity_provider, temp_files):
        """Test finding files similar to a given file."""
        file_path = temp_files["files"][0]  # Python/ML file

        # Mock the open function to return the file content
        with patch(
            "builtins.open",
            return_value=MagicMock(
                __enter__=MagicMock(
                    return_value=MagicMock(
                        read=MagicMock(
                            return_value="This is a Python file about machine learning concepts."
                        )
                    )
                ),
                __exit__=MagicMock(),
            ),
        ):
            results = await similarity_provider.find_similar_files(
                file_path=file_path, threshold=0.5, max_results=3
            )

        # Should return results
        assert len(results) > 0

        # Each result should be a tuple of (path, score)
        for result in results:
            path, score = result
            assert isinstance(path, str)
            assert isinstance(score, float)
            assert 0.0 <= score <= 1.0

    @pytest.mark.asyncio
    async def test_find_file_groups(self, similarity_provider, temp_files):
        """Test finding groups of similar files."""

        # Mock the process_file method to return predetermined embeddings
        async def mock_process_file(file_path):
            if (
                "file1" in str(file_path)
                or "file2" in str(file_path)
                or "file4" in str(file_path)
            ):
                # Python/ML group
                return (file_path, np.array([0.1, 0.8, 0.1], dtype="float32"))
            elif "file3" in str(file_path) or "file5" in str(file_path):
                # JavaScript/web group
                return (file_path, np.array([0.8, 0.1, 0.1], dtype="float32"))
            else:
                return None

        # We need to patch and override the process_file method
        with patch.object(
            similarity_provider, "_process_file", side_effect=mock_process_file
        ):
            # Use monkeypatch to override the batch_processor.process_batch method
            with patch.object(
                similarity_provider.batch_processor,
                "process_batch",
                new=lambda items, process_func, **kwargs: asyncio.gather(
                    *[process_func(item) for item in items]
                ),
            ):
                results = await similarity_provider.find_file_groups(
                    file_paths=temp_files["files"], threshold=0.7, min_group_size=2
                )

        # Should find 2 groups (Python/ML and JavaScript/web)
        assert len(results) > 0

        # Each group should be a list of file paths
        for group in results:
            assert isinstance(group, list)
            assert len(group) >= 2  # Min group size is 2

            # All paths should be strings
            for path in group:
                assert isinstance(path, str)

    @pytest.mark.asyncio
    async def test_cache_usage(self, similarity_provider):
        """Test that results are cached and retrieved from cache."""
        # Set up mock cache to return a cached result
        mock_cache = MagicMock()
        mock_cache.get.return_value = ["cached_file.txt"]

        # Override the provider's cache manager
        similarity_provider.cache_manager = mock_cache

        # Call the search method
        results = await similarity_provider.search(
            query="Test query", threshold=0.5, max_results=3
        )

        # Should return the cached result
        assert results == ["cached_file.txt"]

        # Verify that cache.get was called with the expected key
        mock_cache.get.assert_called_once()

        # The key should contain the query, threshold, and max_results
        key = mock_cache.get.call_args[0][0]
        assert "Test query" in key
        assert "0.5" in key
        assert "3" in key

    @pytest.mark.asyncio
    async def test_empty_results_conditions(self, similarity_provider):
        """Test conditions that should return empty results."""
        # Test with no embedding model
        similarity_provider.embedding_model = None
        results = await similarity_provider.search("test")
        assert results == []

        # Restore embedding model but set vector_index to None
        similarity_provider.embedding_model = MagicMock()
        similarity_provider.vector_index = None
        results = await similarity_provider.search("test")
        assert results == []

        # Test with empty query
        similarity_provider.vector_index = MagicMock()
        results = await similarity_provider.search("")
        assert results == []
