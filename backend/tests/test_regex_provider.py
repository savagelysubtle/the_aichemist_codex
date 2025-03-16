"""Tests for the regex search provider."""

import os
import tempfile
from collections.abc import Generator
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from backend.src.search.providers.regex_provider import RegexSearchProvider
from backend.src.utils.cache_manager import CacheManager


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
    """Create a RegexSearchProvider instance."""
    mock_cache = MagicMock(spec=CacheManager)
    return RegexSearchProvider(cache_manager=mock_cache)


class TestRegexSearchProvider:
    """Test cases for the RegexSearchProvider class."""

    @pytest.mark.asyncio
    async def test_basic_search(
        self,
        regex_provider: RegexSearchProvider,
        temp_files: dict[str, Any],
    ) -> None:
        """Test basic regex search functionality."""
        results = await regex_provider.search(
            query="pattern123", file_paths=temp_files["files"], max_results=10
        )

        # Should match file1, file4, and file6
        assert len(results) == 3  # noqa: S101
        assert str(temp_files["files"][0]) in results  # noqa: S101  # file1
        assert str(temp_files["files"][3]) in results  # noqa: S101  # file4
        assert str(temp_files["files"][5]) in results  # noqa: S101  # file6

    @pytest.mark.asyncio
    async def test_case_sensitive_search(
        self,
        regex_provider: RegexSearchProvider,
        temp_files: dict[str, list[Path]],
    ) -> None:
        """Test case-sensitive regex search."""
        # Case-sensitive search should only match lowercase "pattern123"
        results = await regex_provider.search(
            query="pattern123",
            file_paths=temp_files["files"],
            max_results=10,
            case_sensitive=True,
        )

        assert len(results) == 3  # noqa: S101
        assert str(temp_files["files"][0]) in results  # noqa: S101  # file1
        assert str(temp_files["files"][3]) in results  # noqa: S101  # file4
        assert str(temp_files["files"][5]) in results  # noqa: S101  # file6

        # Case-sensitive search for uppercase "PATTERN123"
        results = await regex_provider.search(
            query="PATTERN123",
            file_paths=temp_files["files"],
            max_results=10,
            case_sensitive=True,
        )

        assert len(results) == 1  # noqa: S101
        assert str(temp_files["files"][1]) in results  # noqa: S101  # file2

    @pytest.mark.asyncio
    async def test_whole_word_search(
        self,
        regex_provider: RegexSearchProvider,
        temp_files: dict[str, Path | list[Path]],
    ) -> None:
        """Test whole word regex search."""
        # Create a file with "pattern123" as part of a larger word
        dir_path = temp_files["dir"]
        assert isinstance(dir_path, Path), "dir_path must be a Path object"  # noqa: S101
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", dir=dir_path, delete=False
        ) as f:
            f.write(
                "This contains mypattern123suffix which shouldn't match whole word."
            )
            temp_file = Path(f.name)

        try:
            # Search with whole_word=True
            files = temp_files["files"]
            assert isinstance(files, list), "files must be a list"  # noqa: S101
            results = await regex_provider.search(
                query="pattern123",
                file_paths=files + [temp_file],
                max_results=10,
                whole_word=True,
            )

            # Should match file1, file4, and file6 but not the new temp file
            assert len(results) == 3  # noqa: S101
            assert str(temp_file) not in results  # noqa: S101

        finally:
            # Clean up
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    @pytest.mark.asyncio
    async def test_complex_regex(
        self,
        regex_provider: RegexSearchProvider,
        temp_files: dict[str, Path | list[Path]],
    ) -> None:
        """Test more complex regex patterns."""
        # Create a file with email addresses
        dir_path = temp_files["dir"]
        assert isinstance(dir_path, Path), "dir_path must be a Path object"  # noqa: S101
        email_file = Path(dir_path) / "emails.txt"
        email_file.write_text(
            """
        Contact us at:
        john.doe@example.com
        jane.smith@company.org
        support@test-site.co.uk
        """
        )

        # Search for email pattern
        files = temp_files["files"]
        assert isinstance(files, list), "files must be a list"  # noqa: S101
        results = await regex_provider.search(
            query=r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            file_paths=files + [email_file],
            max_results=10,
        )

        assert len(results) == 1  # noqa: S101
        assert str(email_file) in results  # noqa: S101

    @pytest.mark.asyncio
    async def test_max_results(
        self,
        regex_provider: RegexSearchProvider,
        temp_files: dict[str, Path | list[Path]],
    ) -> None:
        """Test max_results parameter."""
        files = temp_files["files"]
        assert isinstance(files, list), "files must be a list"  # noqa: S101
        results = await regex_provider.search(
            query="pattern123", file_paths=files, max_results=2
        )

        # Should only return 2 results even though there are 3 matching files
        assert len(results) == 2  # noqa: S101

    @pytest.mark.asyncio
    async def test_invalid_regex(
        self,
        regex_provider: RegexSearchProvider,
        temp_files: dict[str, Path | list[Path]],
    ) -> None:
        """Test handling of invalid regex patterns."""
        # This is an invalid regex pattern (unclosed parenthesis)
        files = temp_files["files"]
        assert isinstance(files, list), "files must be a list"  # noqa: S101
        results = await regex_provider.search(
            query="pattern(123", file_paths=files, max_results=10
        )

        # Should return empty list for invalid pattern
        assert results == []  # noqa: S101

    @pytest.mark.asyncio
    async def test_binary_file_handling(
        self,
        regex_provider: RegexSearchProvider,
        temp_files: dict[str, Path | list[Path]],
    ) -> None:
        """Test that binary files are properly handled."""
        files = temp_files["files"]
        assert isinstance(files, list), "files must be a list"  # noqa: S101
        binary_file = files[4]  # binary.bin

        # Try to search in all files including the binary one
        results = await regex_provider.search(
            query="pattern", file_paths=files, max_results=10
        )

        # Binary file should be skipped
        assert str(binary_file) not in results  # noqa: S101

    @pytest.mark.asyncio
    async def test_caching(self, temp_files: dict[str, Path | list[Path]]) -> None:
        """Test that search results are cached."""
        # Create a real cache manager for this test
        cache_manager = CacheManager()
        provider = RegexSearchProvider(cache_manager=cache_manager)

        # First search should cache the results
        query = "pattern123"
        file_paths = temp_files["files"]
        assert isinstance(file_paths, list), "file_paths must be a list"  # noqa: S101

        results1 = await provider.search(
            query=query, file_paths=file_paths, max_results=10
        )

        # Modify one of the files to contain the pattern
        files = temp_files["files"]
        assert isinstance(files, list), "files must be a list"  # noqa: S101
        files[2].write_text("Now this file has pattern123 in it")

        # Second search with same parameters should return cached results
        results2 = await provider.search(
            query=query, file_paths=file_paths, max_results=10
        )

        # Results should be the same despite the file change
        assert results1 == results2  # noqa: S101
        assert len(results1) == 3  # noqa: S101  # Still 3 results from before

        # Clear cache and search again
        cache_key = (
            f"regex_search:{query}:{','.join(sorted(str(p) for p in file_paths))}"
        )
        await cache_manager.invalidate(cache_key)

        results3 = await provider.search(
            query=query, file_paths=file_paths, max_results=10
        )

        # Now we should get 4 results including the modified file
        assert len(results3) == 4  # noqa: S101
        files = temp_files["files"]
        assert isinstance(files, list), "files must be a list"  # noqa: S101
        assert str(files[2]) in results3  # noqa: S101
