"""Tests for metadata extraction functionality."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from backend.file_reader.file_metadata import FileMetadata
from backend.metadata.code_extractor import CodeMetadataExtractor
from backend.metadata.document_extractor import DocumentMetadataExtractor
from backend.metadata.manager import MetadataManager
from backend.metadata.text_extractor import TextMetadataExtractor
from backend.utils.cache_manager import CacheManager


@pytest.fixture
def sample_text_file(tmp_path):
    """Create a sample text file for testing."""
    content = """
    # Sample Text File

    Author: Test Author
    Date: 2023-01-15

    This is a sample text file used for testing the metadata extraction functionality.
    It contains keywords like python, testing, metadata, and extraction.

    The text contains some URLs like https://example.com and email addresses like test@example.com.
    """
    file_path = tmp_path / "sample.txt"
    file_path.write_text(content)
    return file_path


@pytest.fixture
def sample_python_file(tmp_path):
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
def sample_markdown_file(tmp_path):
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
def mock_cache_manager():
    """Create a mock cache manager."""
    cache_manager = MagicMock(spec=CacheManager)
    cache_manager.get.return_value = None
    return cache_manager


@pytest.mark.asyncio
async def test_text_metadata_extraction(sample_text_file, mock_cache_manager):
    """Test metadata extraction for text files."""
    # Create an extractor instance
    extractor = TextMetadataExtractor(cache_manager=mock_cache_manager)

    # Extract metadata
    metadata = await extractor.extract(sample_text_file)

    # Check basic extraction results
    assert metadata["extraction_complete"] is True
    assert metadata["extraction_confidence"] > 0

    # Check text-specific metadata
    assert metadata["language"] == "en"  # Should detect English
    assert len(metadata["keywords"]) > 0
    assert len(metadata["tags"]) > 0

    # Check entity extraction
    assert "contains-urls" in metadata["tags"]
    assert "contains-emails" in metadata["entities"]["emails"]
    assert "https://example.com" in metadata["entities"]["urls"]
    assert "test@example.com" in metadata["entities"]["emails"]


@pytest.mark.asyncio
async def test_code_metadata_extraction(sample_python_file, mock_cache_manager):
    """Test metadata extraction for code files."""
    # Create an extractor instance
    extractor = CodeMetadataExtractor(cache_manager=mock_cache_manager)

    # Extract metadata
    metadata = await extractor.extract(sample_python_file)

    # Check basic extraction results
    assert metadata["extraction_complete"] is True
    assert metadata["extraction_confidence"] > 0

    # Check code-specific metadata
    assert metadata["code_language"] == "python"
    assert "os" in metadata["imports"]
    assert "sys" in metadata["imports"]
    assert "numpy" in metadata["imports"] or "np" in metadata["imports"]

    # Check functions and classes
    assert "sample_function" in metadata["functions"]
    assert "SampleClass" in metadata["classes"]

    # Check tags
    assert "lang:python" in metadata["tags"]
    assert "data-science" in metadata["tags"]  # Due to numpy and pandas imports


@pytest.mark.asyncio
async def test_document_metadata_extraction(sample_markdown_file, mock_cache_manager):
    """Test metadata extraction for document files."""
    # Create an extractor instance
    extractor = DocumentMetadataExtractor(cache_manager=mock_cache_manager)

    # Extract metadata
    metadata = await extractor.extract(sample_markdown_file)

    # Check basic extraction results
    assert metadata["extraction_complete"] is True
    assert metadata["extraction_confidence"] > 0

    # Check document-specific metadata
    assert (
        metadata["title"] == "Metadata Extraction Testing"
    )  # Should extract the first heading
    assert "Test Author" in metadata["authors"]
    assert "1.0.0" in metadata["version"]

    # Check statistics
    assert metadata["statistics"]["word_count"] > 0
    assert (
        metadata["statistics"]["section_count"] >= 4
    )  # Should count 4 sections from headings


@pytest.mark.asyncio
async def test_metadata_manager_single_file(sample_python_file, mock_cache_manager):
    """Test the metadata manager with a single file."""
    # Create a metadata manager
    manager = MetadataManager(cache_manager=mock_cache_manager)

    # Extract metadata
    metadata = await manager.extract_metadata(sample_python_file)

    # Check the result is a FileMetadata object
    assert isinstance(metadata, FileMetadata)

    # Check basic properties
    assert metadata.path == str(sample_python_file)
    assert metadata.mime_type is not None
    assert metadata.size > 0
    assert metadata.extension == ".py"

    # Check enhanced metadata
    assert metadata.code_language == "python"
    assert len(metadata.imports) > 0
    assert len(metadata.functions) > 0
    assert len(metadata.classes) > 0
    assert len(metadata.tags) > 0
    assert metadata.extraction_complete is True


@pytest.mark.asyncio
async def test_metadata_manager_batch_extraction(tmp_path, mock_cache_manager):
    """Test batch metadata extraction."""
    # Create sample files
    (tmp_path / "file1.txt").write_text("This is a test file.")
    (tmp_path / "file2.py").write_text("def test(): return 'test'")
    (tmp_path / "file3.md").write_text("# Test Markdown\n\nThis is a test.")

    # Create a list of file paths
    file_paths = [tmp_path / "file1.txt", tmp_path / "file2.py", tmp_path / "file3.md"]

    # Create a metadata manager
    manager = MetadataManager(cache_manager=mock_cache_manager)

    # Extract metadata in batch
    results = await manager.extract_batch(file_paths)

    # Check results
    assert len(results) == 3
    assert all(isinstance(result, FileMetadata) for result in results)
    assert all(result.extraction_complete for result in results)

    # Check file-specific results
    file_results = {Path(result.path).name: result for result in results}

    assert "file1.txt" in file_results
    assert "file2.py" in file_results
    assert "file3.md" in file_results

    # Check Python file metadata
    assert file_results["file2.py"].code_language == "python"
    assert "test" in file_results["file2.py"].functions

    # Check Markdown file metadata
    assert file_results["file3.md"].title == "Test Markdown"
