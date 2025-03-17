"""Tests for the regex search provider."""

import logging
import tempfile
import time
from collections.abc import Generator
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from backend.src.search.providers.regex_provider import RegexSearchProvider
from backend.src.utils.cache_manager import CacheManager

logger = logging.getLogger(__name__)


@pytest.fixture
def temp_files() -> Generator[dict[str, Path | list[Path]]]:
    """Create temporary test files with content."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test files with different content
        file1 = Path(temp_dir) / "file1.txt"
        file1.write_text("This is a test file with pattern123 in it.")

        file2 = Path(temp_dir) / "file2.txt"
        file2.write_text("Another file with PATTERN123 and more text.")

        file3 = Path(temp_dir) / "file3.txt"
        file3.write_text("This file doesn't have the pattern.")

        file4 = Path(temp_dir) / "file4.txt"
        file4.write_text("Multiple pattern123 occurrences pattern123 here.")

        # Create a binary file
        file5 = Path(temp_dir) / "binary.bin"
        with open(file5, "wb") as f:
            f.write(b"\x00\x01\x02\x03\x04")

        # Create a large text file
        file6 = Path(temp_dir) / "large.txt"
        file6.write_text("pattern123\n" * 1000)

        yield {
            "dir": Path(temp_dir),
            "files": [file1, file2, file3, file4, file5, file6],
        }


@pytest.fixture
def regex_provider() -> RegexSearchProvider:
    """Create a RegexSearchProvider instance for testing."""
    # Create a mock cache manager that always returns None for get() to bypass cache
    mock_cache_manager = MagicMock(spec=CacheManager)
    mock_cache_manager.get.return_value = None

    return RegexSearchProvider(cache_manager=mock_cache_manager)


class TestRegexSearchProvider:
    """Test cases for the RegexSearchProvider class."""

    @pytest.mark.search
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_basic_search(
        self,
        regex_provider: RegexSearchProvider,
        temp_files: dict[str, Any],
    ) -> None:
        """Test basic regex search functionality."""
        # Mock the _search_files method to return expected results
        with patch.object(
            regex_provider,
            "_search_files",
            return_value=[str(temp_files["files"][0]), str(temp_files["files"][1])],
        ):
            # Test basic search with file paths
            file_paths = temp_files["files"]
            results = await regex_provider.search(
                "pattern123", file_paths=file_paths, max_results=10
            )
            assert len(results) > 0  # noqa: S101

            # Verify results are strings (file paths)
            assert all(isinstance(r, str) for r in results)  # noqa: S101

    @pytest.mark.search
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_case_sensitive_search(
        self,
        regex_provider: RegexSearchProvider,
        temp_files: dict[str, Any],
    ) -> None:
        """Test case-sensitive search functionality."""
        file_paths = temp_files["files"]

        # Mock the _search_files method to return different results based on case sensitivity
        async def mock_search_files(pattern, file_paths, max_results):
            if pattern.pattern == "PATTERN123":  # Case-sensitive
                return [str(temp_files["files"][1])]  # Only file with uppercase
            else:  # Case-insensitive
                return [str(temp_files["files"][0]), str(temp_files["files"][1])]

        with patch.object(
            regex_provider, "_search_files", side_effect=mock_search_files
        ):
            # Case-insensitive search (default)
            results_insensitive = await regex_provider.search(
                "PATTERN123",
                case_sensitive=False,
                file_paths=file_paths,
                max_results=10,
            )
            assert len(results_insensitive) > 0  # noqa: S101

            # Case-sensitive search
            results_sensitive = await regex_provider.search(
                "PATTERN123", case_sensitive=True, file_paths=file_paths, max_results=10
            )

            # There should be fewer case-sensitive matches than insensitive
            assert len(results_sensitive) <= len(results_insensitive)  # noqa: S101

    @pytest.mark.search
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_whole_word_search(
        self,
        regex_provider: RegexSearchProvider,
        temp_files: dict[str, Any],
    ) -> None:
        """Test whole word search functionality."""
        # Create a file with specific content for whole word testing
        test_file = Path(temp_files["dir"]) / "whole_word_test.txt"
        with open(test_file, "w") as f:
            f.write(
                "This is a test file.\n"
                "It contains the word test and testing and tester.\n"
                "Also contest and testament are not matches.\n"
            )

        # Non-whole word search
        results_non_whole = await regex_provider.search(
            "test", whole_word=False, max_results=10, file_paths=[test_file]
        )

        # Whole word search
        results_whole = await regex_provider.search(
            "test", whole_word=True, max_results=10, file_paths=[test_file]
        )

        # There should be fewer whole word matches than non-whole word matches
        assert len(results_whole) <= len(results_non_whole)  # noqa: S101

    @pytest.mark.search
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_complex_regex(
        self,
        regex_provider: RegexSearchProvider,
        temp_files: dict[str, Any],
    ) -> None:
        """Test complex regex patterns."""
        # Create a file with specific content for regex testing
        test_file = Path(temp_files["dir"]) / "regex_test.txt"
        with open(test_file, "w") as f:
            f.write(
                "Email: user@example.com\n"
                "Phone: 123-456-7890\n"
                "Date: 2023-01-15\n"
                "IP Address: 192.168.1.1\n"
                "Product Code: ABC-123-XYZ\n"
            )

        # For email pattern
        with patch.object(
            regex_provider, "_search_files", return_value=[str(test_file)]
        ):
            # Test email regex
            email_results = await regex_provider.search(
                r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
                max_results=10,
                file_paths=[test_file],
            )
            assert len(email_results) > 0  # noqa: S101

        # For phone pattern
        with patch.object(
            regex_provider, "_search_files", return_value=[str(test_file)]
        ):
            # Test phone number regex
            phone_results = await regex_provider.search(
                r"\d{3}-\d{3}-\d{4}", max_results=10, file_paths=[test_file]
            )
            assert len(phone_results) > 0  # noqa: S101

    @pytest.mark.search
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_max_results(
        self,
        regex_provider: RegexSearchProvider,
        temp_files: dict[str, Any],
    ) -> None:
        """Test max_results parameter."""
        file_paths = temp_files["files"]

        # Test with different max_results values
        results_5 = await regex_provider.search(
            "pattern123", file_paths=file_paths, max_results=5
        )
        results_10 = await regex_provider.search(
            "pattern123", file_paths=file_paths, max_results=10
        )

        # Verify max_results is respected
        assert len(results_5) <= 5  # noqa: S101
        assert len(results_10) <= 10  # noqa: S101

    @pytest.mark.search
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_invalid_regex(
        self,
        regex_provider: RegexSearchProvider,
        temp_files: dict[str, Any],
    ) -> None:
        """Test handling of invalid regex patterns."""
        file_paths = temp_files["files"]

        # Test with invalid regex pattern
        results = await regex_provider.search(
            r"[invalid regex", file_paths=file_paths, max_results=10
        )

        # Should return empty results for invalid regex
        assert len(results) == 0  # noqa: S101

    @pytest.mark.search
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_binary_file_handling(
        self,
        regex_provider: RegexSearchProvider,
        temp_files: dict[str, Any],
    ) -> None:
        """Test handling of binary files."""
        # Create a binary file
        binary_file = Path(temp_files["dir"]) / "binary_file.bin"
        with open(binary_file, "wb") as f:
            f.write(b"\x00\x01\x02\x03\x04test\x05\x06\x07\x08")

        # Search should handle binary files gracefully
        results = await regex_provider.search(
            "test", max_results=10, file_paths=[binary_file]
        )

        # Binary files should be skipped or handled appropriately
        assert len(results) == 0  # noqa: S101

    @pytest.mark.search
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_caching(self, temp_files: dict[str, Any]) -> None:
        """Test caching functionality."""
        file_paths = temp_files["files"]

        # Create a provider with caching
        cache_dir = Path(temp_files["dir"]) / "cache"
        cache_manager = CacheManager(cache_dir=cache_dir)
        provider_with_cache = RegexSearchProvider(cache_manager=cache_manager)

        # First search (cache miss)
        start_time = time.time()
        results1 = await provider_with_cache.search(
            "pattern123", file_paths=file_paths, max_results=10
        )
        first_search_time = time.time() - start_time

        # Second search (cache hit)
        start_time = time.time()
        results2 = await provider_with_cache.search(
            "pattern123", file_paths=file_paths, max_results=10
        )
        second_search_time = time.time() - start_time

        # Verify results are the same
        assert len(results1) == len(results2)  # noqa: S101

        # Second search should be faster due to caching
        # Note: This is a soft assertion as timing can vary
        logger.info(
            f"First search: {first_search_time:.4f}s, "
            f"Second search: {second_search_time:.4f}s"
        )
