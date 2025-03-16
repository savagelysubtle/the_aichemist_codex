"""Tests for metadata extraction functionality."""

from pathlib import Path
from typing import cast
from unittest.mock import MagicMock

import pytest

from backend.src.file_reader.file_metadata import FileMetadata
from backend.src.metadata.code_extractor import CodeMetadataExtractor
from backend.src.metadata.document_extractor import DocumentMetadataExtractor
from backend.src.metadata.manager import MetadataManager
from backend.src.metadata.text_extractor import TextMetadataExtractor
from backend.src.utils.cache_manager import CacheManager


@pytest.fixture
def sample_text_file(tmp_path: Path) -> Path:
    """Create a sample text file for testing."""
    content = """
    # Sample Text File

    Author: Test Author
    Date: 2023-01-15

    This is a sample text file used for testing the metadata extraction functionality.
    It contains keywords like python, testing, metadata, and extraction.

    The text contains some URLs like https://example.com
    and email addresses like test@example.com.
    """
    file_path = tmp_path / "sample.txt"
    file_path.write_text(content)
    return file_path


@pytest.fixture
def sample_python_file(tmp_path: Path) -> Path:
    """Create a sample Python file for testing."""
    content = """#!/usr/bin/env python
    # -*- coding: utf-8 -*-

    \"\"\"
    Sample Python module for testing metadata extraction.

    This module provides testing functionality.
    \"\"\"

    import os
    import sys
    from pathlib import Path
    import numpy as np
    import pandas as pd


    class SampleClass:
        \"\"\"A sample class for testing.\"\"\"

        def __init__(self, name):
            \"\"\"Initialize with a name.\"\"\"
            self.name = name

        def process(self, data):
            \"\"\"Process the given data.\"\"\"
            if data is None:
                return []

            result = []
            for item in data:
                result.append(item * 2)

            return result


    def sample_function(parameter1, parameter2=None):
        \"\"\"A sample function for testing.

        Args:
            parameter1: The first parameter
            parameter2: The second parameter (optional)

        Returns:
            The result of processing
        \"\"\"
        if parameter2 is None:
            return parameter1

        return parameter1 + parameter2


    if __name__ == "__main__":
        sample = SampleClass("test")
        result = sample.process([1, 2, 3])
        print(f"Result: {result}")
    """
    file_path = tmp_path / "sample.py"
    file_path.write_text(content)
    return file_path


@pytest.fixture
def sample_markdown_file(tmp_path: Path) -> Path:
    """Create a sample Markdown file for testing."""
    content = """# Metadata Extraction Testing

    ## Introduction

    This document is used to test the metadata extraction capabilities of the system.

    ## Features

    - Feature 1
    - Feature 2
    - Feature 3

    ## Author Information

    Created by: Test Author
    Last Updated: January 20, 2023
    Version: 1.0.0

    ## Conclusion

    This is a sample conclusion for the document.
    """
    file_path = tmp_path / "sample.md"
    file_path.write_text(content)
    return file_path


@pytest.fixture
def mock_cache_manager() -> MagicMock:
    """Create a mock cache manager."""
    cache_manager = MagicMock(spec=CacheManager)
    cache_manager.get.return_value = None
    return cache_manager


@pytest.mark.asyncio
async def test_text_metadata_extraction(
    sample_text_file: Path, mock_cache_manager: MagicMock
) -> None:
    """Test metadata extraction for text files."""
    # Create an extractor instance
    extractor = TextMetadataExtractor(cache_manager=mock_cache_manager)

    # Extract metadata
    metadata = await extractor.extract(sample_text_file)

    # Check basic extraction results
    assert metadata["extraction_complete"] is True  # noqa: S101
    assert metadata["extraction_confidence"] > 0  # noqa: S101

    # Check text-specific metadata
    assert metadata["language"] == "en"  # noqa: S101 Should detect English
    assert len(metadata["keywords"]) > 0  # noqa: S101
    assert len(metadata["tags"]) > 0  # noqa: S101

    # Check entity extraction
    assert "contains-urls" in metadata["tags"]  # noqa: S101
    assert "contains-emails" in metadata["entities"]["emails"]  # noqa: S101
    assert "https://example.com" in metadata["entities"]["urls"]  # noqa: S101
    assert "test@example.com" in metadata["entities"]["emails"]  # noqa: S101


@pytest.mark.asyncio
async def test_code_metadata_extraction(
    sample_python_file: Path,
    mock_cache_manager: MagicMock,
) -> None:
    """Test metadata extraction for code files."""
    # Create an extractor instance
    extractor = CodeMetadataExtractor(cache_manager=mock_cache_manager)

    # Extract metadata
    metadata = await extractor.extract(sample_python_file)

    # Check basic extraction results
    assert metadata["extraction_complete"] is True  # noqa: S101
    assert metadata["extraction_confidence"] > 0  # noqa: S101

    # Check code-specific metadata
    assert metadata["code_language"] == "python"  # noqa: S101
    assert "os" in metadata["imports"]  # noqa: S101
    assert "sys" in metadata["imports"]  # noqa: S101
    assert "numpy" in metadata["imports"] or "np" in metadata["imports"]  # noqa: S101

    # Check functions and classes
    assert "sample_function" in metadata["functions"]  # noqa: S101
    assert "SampleClass" in metadata["classes"]  # noqa: S101

    # Check tags
    assert "lang:python" in metadata["tags"]  # noqa: S101
    assert "data-science" in metadata["tags"]  # noqa: S101 Due to numpy and pandas imports


@pytest.mark.asyncio
async def test_document_metadata_extraction(
    sample_markdown_file: Path,
    mock_cache_manager: MagicMock,
) -> None:
    """Test metadata extraction for document files."""
    # Create an extractor instance
    extractor = DocumentMetadataExtractor(cache_manager=mock_cache_manager)

    # Extract metadata
    metadata = await extractor.extract(sample_markdown_file)

    # Check basic extraction results
    assert metadata["extraction_complete"] is True  # noqa: S101
    assert metadata["extraction_confidence"] > 0  # noqa: S101

    # Check document-specific metadata
    assert (  # noqa: S101
        metadata["title"] == "Metadata Extraction Testing"
    )  # Should extract the first heading
    assert "Test Author" in metadata["authors"]  # noqa: S101
    assert "1.0.0" in metadata["version"]  # noqa: S101

    # Check statistics
    assert metadata["statistics"]["word_count"] > 0  # noqa: S101
    assert (  # noqa: S101
        metadata["statistics"]["section_count"] >= 4
    )  # Should count 4 sections from headings


@pytest.mark.asyncio
async def test_metadata_manager_single_file(
    sample_python_file: Path,
    mock_cache_manager: MagicMock,
) -> None:
    """Test the metadata manager with a single file."""
    # Create a metadata manager
    manager = MetadataManager(cache_manager=mock_cache_manager)

    # Extract metadata
    metadata = await manager.extract_metadata(sample_python_file)

    # Check the result is a FileMetadata object
    assert isinstance(metadata, FileMetadata)  # noqa: S101

    # Check basic properties
    assert metadata.path == str(sample_python_file)  # noqa: S101
    assert metadata.mime_type is not None  # noqa: S101
    assert metadata.size > 0  # noqa: S101
    assert metadata.extension == ".py"  # noqa: S101

    # Check enhanced metadata
    assert metadata.programming_language == "python"  # noqa: S101
    assert len(metadata.imports) > 0  # noqa: S101
    assert len(metadata.functions) > 0  # noqa: S101
    assert len(metadata.classes) > 0  # noqa: S101
    assert len(metadata.tags) > 0  # noqa: S101
    assert metadata.extraction_complete is True  # noqa: S101


@pytest.mark.asyncio
async def test_metadata_manager_batch_extraction(
    tmp_path: Path,
    mock_cache_manager: MagicMock,
) -> None:
    """Test batch metadata extraction."""
    # Create sample files
    (tmp_path / "file1.txt").write_text("This is a test file.")
    (tmp_path / "file2.py").write_text("def test(): return 'test'")
    (tmp_path / "file3.md").write_text("# Test Markdown\n\nThis is a test.")

    # Create a tuple of file paths and cast to expected type
    paths = (
        tmp_path / "file1.txt",
        tmp_path / "file2.py",
        tmp_path / "file3.md",
    )
    file_paths = cast(list[str | Path], list(paths))

    # Create a metadata manager
    manager = MetadataManager(cache_manager=mock_cache_manager)

    # Extract metadata in batch
    results = await manager.extract_batch(file_paths)

    # Check results
    assert len(results) == 3  # noqa: S101
    assert all(isinstance(result, FileMetadata) for result in results)  # noqa: S101
    assert all(result.extraction_complete for result in results)  # noqa: S101

    # Check file-specific results
    file_results = {Path(result.path).name: result for result in results}

    assert "file1.txt" in file_results  # noqa: S101
    assert "file2.py" in file_results  # noqa: S101
    assert "file3.md" in file_results  # noqa: S101

    # Check Python file metadata
    assert file_results["file2.py"].programming_language == "python"  # noqa: S101
    assert "test" in file_results["file2.py"].functions  # noqa: S101

    # Check Markdown file metadata
    assert file_results["file3.md"].title == "Test Markdown"  # noqa: S101
