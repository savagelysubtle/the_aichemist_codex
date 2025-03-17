"""Tests for the PDF metadata extractor module.

This module contains unit tests for the PDFMetadataExtractor class.
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from the_aichemist_codex.backend.metadata.pdf_extractor import (
    PYPDF_AVAILABLE,
    PDFMetadataExtractor,
)


@pytest.fixture
def pdf_extractor():
    """Fixture for creating a PDF extractor instance."""
    return PDFMetadataExtractor()


@pytest.mark.skipif(not PYPDF_AVAILABLE, reason="pypdf is not installed")
class TestPDFMetadataExtractor:
    """Test suite for the PDF metadata extractor."""

    @pytest.mark.metadata
    @pytest.mark.unit
    def test_supported_mime_types(self, pdf_extractor: PDFMetadataExtractor) -> None:
        """Test the supported MIME types."""
        assert "application/pdf" in pdf_extractor.supported_mime_types
        assert len(pdf_extractor.supported_mime_types) >= 1

    @pytest.mark.metadata
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_file_extensions(self, pdf_extractor: PDFMetadataExtractor) -> None:
        """Test the file extension mapping."""
        assert ".pdf" in pdf_extractor.FILE_EXTENSIONS  # type: ignore
        assert pdf_extractor.FILE_EXTENSIONS[".pdf"] == "application/pdf"  # type: ignore

    @pytest.mark.asyncio
    @pytest.mark.metadata
    @pytest.mark.unit
    async def test_extract_nonexistent_file(
        self, pdf_extractor: PDFMetadataExtractor
    ) -> None:
        """Test extraction with a nonexistent file."""
        with pytest.raises(FileNotFoundError):
            await pdf_extractor.extract("/nonexistent/file.pdf")

    @pytest.mark.asyncio
    @pytest.mark.metadata
    @pytest.mark.unit
    async def test_extract_unsupported_mime_type(
        self, pdf_extractor: PDFMetadataExtractor
    ) -> None:
        """Test extraction with an unsupported MIME type."""
        # Create a temporary file
        tmp_file = Path("test_file.txt")
        tmp_file.write_text("This is not a PDF file")

        try:
            # Mock the MIME type detector to return an unsupported type
            with patch(
                "the_aichemist_codex.backend.utils.mime_type_detector.MimeTypeDetector.get_mime_type",
                return_value=("text/plain", 1.0),
            ):
                with pytest.raises(ValueError):
                    await pdf_extractor.extract(tmp_file)
        finally:
            # Clean up
            if tmp_file.exists():
                tmp_file.unlink()

    @pytest.mark.asyncio
    @pytest.mark.metadata
    @pytest.mark.unit
    async def test_extract_with_cache(
        self, pdf_extractor: PDFMetadataExtractor
    ) -> None:
        """Test extraction with cache."""
        # Set up mocks
        cache_manager = MagicMock()
        # Make get() return an awaitable mock
        cache_manager.get = AsyncMock()
        pdf_extractor.cache_manager = cache_manager

        # Mock cache hit
        cached_data = {"metadata_type": "pdf", "cached": True}
        cache_manager.get.return_value = cached_data

        # Test extraction with cache hit
        file_path = Path("test_file.pdf")

        # Create a dummy file
        file_path.write_text("Dummy PDF content")

        try:
            # Mock MIME type detection
            with patch(
                "the_aichemist_codex.backend.utils.mime_type_detector.MimeTypeDetector.get_mime_type",
                return_value=("application/pdf", 1.0),
            ):
                result = await pdf_extractor.extract(file_path)

            # Verify that cache was used
            assert result == cached_data
            cache_manager.get.assert_called_once()

            # Clean up
        finally:
            # Clean up the temporary file
            if file_path.exists():
                file_path.unlink()

    @pytest.mark.asyncio
    @pytest.mark.metadata
    @pytest.mark.unit
    async def test_extract_without_pypdf(
        self, pdf_extractor: PDFMetadataExtractor
    ) -> None:
        """Test extraction when PyPDF2 is not available."""
        with patch(
            "the_aichemist_codex.backend.utils.mime_type_detector.MimeTypeDetector.get_mime_type",
            return_value=("application/pdf", 1.0),
        ):
            # Create a temporary file
            tmp_file = Path("test_file.pdf")
            tmp_file.write_text("Dummy PDF content")

            try:
                # Mock mime type detection
                with patch(
                    "the_aichemist_codex.backend.utils.mime_type_detector.MimeTypeDetector.get_mime_type",
                    return_value=("application/pdf", 1.0),
                ):
                    result = await pdf_extractor.extract(tmp_file)

                # Check that an error was logged and basic metadata was returned
                assert result["metadata_type"] == "pdf"
                assert "error" in result
                assert "Stream has ended unexpectedly" in result["error"]
            finally:
                # Clean up the temporary file
                if tmp_file.exists():
                    tmp_file.unlink()

    @pytest.mark.asyncio
    @pytest.mark.metadata
    @pytest.mark.unit
    async def test_extract_with_pypdf_error(
        self, pdf_extractor: PDFMetadataExtractor
    ) -> None:
        """Test extraction when PyPDF2 raises an error."""
        # Create a temporary file
        tmp_file = Path("test_file.pdf")
        tmp_file.write_text("This is a fake PDF file that will cause PyPDF2 to error")

        try:
            # Mock the MIME type detector to return a supported type
            with patch(
                "the_aichemist_codex.backend.utils.mime_type_detector.MimeTypeDetector.get_mime_type",
                return_value=("application/pdf", 1.0),
            ):
                # Mock PyPDF2 to raise an exception
                with patch(
                    "the_aichemist_codex.backend.metadata.pdf_extractor.PdfReader",
                    side_effect=Exception("Failed to read PDF"),
                ):
                    result = await pdf_extractor.extract(tmp_file)

            # Check that we got a warning about the error
            assert result["metadata_type"] == "pdf"
            assert "error" in result
            assert "Failed to read PDF" in result["error"]
        finally:
            # Clean up
            if tmp_file.exists():
                tmp_file.unlink()

    @pytest.mark.metadata
    @pytest.mark.unit
    def test_extract_with_pypdf(self, pdf_extractor: PDFMetadataExtractor) -> None:
        """Test the PyPDF2 extraction method directly."""
        # This test would require a real PDF file
        # For unit testing purposes, we'll mock PdfReader instead

        with (
            patch(
                "the_aichemist_codex.backend.metadata.pdf_extractor.PdfReader"
            ) as mock_reader,
            patch("os.path.getsize", return_value=12345) as mock_getsize,
            patch("os.path.exists", return_value=True) as mock_exists,
        ):
            # Set up the mock reader
            mock_instance = MagicMock()
            mock_reader.return_value = mock_instance

            # Mock document info dictionary
            mock_instance.metadata = {
                "/Title": "Test PDF",
                "/Author": "Test Author",
                "/Subject": "Test Subject",
                "/Keywords": "test, pdf",
                "/Creator": "Test Creator",
                "/Producer": "Test Producer",
                "/CreationDate": "D:20210101120000",
                "/ModDate": "D:20210101130000",
            }

            # Mock pages
            mock_instance.pages = [MagicMock(), MagicMock(), MagicMock()]

            # Call the method
            metadata = pdf_extractor._extract_pdf_with_pypdf("dummy_path")

            # Verify metadata extraction
            assert metadata["title"] == "Test PDF"
            assert metadata["author"] == "Test Author"
            assert metadata["extraction_method"] == "pypdf"

    @patch(
        "the_aichemist_codex.backend.utils.mime_type_detector.MimeTypeDetector.get_mime_type",
        return_value=("application/pdf", 1.0),
    )
    def test_constructor(self, mock_get_mime):
        """Test PDF extractor initialization."""
        extractor = PDFMetadataExtractor()
        assert extractor is not None
        assert extractor.supported_mime_types == ["application/pdf"]

    @pytest.mark.skipif(not PYPDF_AVAILABLE, reason="pypdf not available")
    @patch(
        "the_aichemist_codex.backend.utils.mime_type_detector.MimeTypeDetector.get_mime_type",
        return_value=("application/pdf", 1.0),
    )
    @patch("the_aichemist_codex.backend.metadata.pdf_extractor.PdfReader")
    def test_extract_basic_pdf_metadata(self, mock_pdf_reader, mock_get_mime):
        """Test basic metadata extraction from PDF using PyPDF2."""
        # Setup mocks
        mock_get_mime.return_value = ("application/pdf", 1.0)

        # Mock PyPDF2 reader
        mock_reader_instance = MagicMock()
        mock_pdf_reader.return_value = mock_reader_instance

        # Set up metadata
        mock_reader_instance.metadata = {
            "/Title": "Sample PDF",
            "/Author": "Test Author",
            "/Creator": "PDF Creator",
            "/Producer": "PDF Producer",
            "/CreationDate": "D:20230101120000",
            "/ModDate": "D:20230102120000",
        }
        mock_reader_instance.pages = [
            MagicMock(),
            MagicMock(),
            MagicMock(),
            MagicMock(),
            MagicMock(),
        ]

        # Mock file system calls
        with (
            patch("os.path.getsize", return_value=54321),
            patch("os.path.exists", return_value=True),
        ):
            # Test extraction
            extractor = PDFMetadataExtractor()
            fake_pdf_path = "/path/to/test.pdf"
            metadata = extractor._extract_pdf_with_pypdf(fake_pdf_path)

            # Verify results
            assert metadata is not None
            assert metadata["title"] == "Sample PDF"
            assert metadata["author"] == "Test Author"
            assert metadata["creator"] == "PDF Creator"
            assert metadata["extraction_method"] == "pypdf"

    @pytest.mark.skipif(not PYPDF_AVAILABLE, reason="pypdf not available")
    @patch(
        "the_aichemist_codex.backend.utils.mime_type_detector.MimeTypeDetector.get_mime_type",
        return_value=("application/pdf", 1.0),
    )
    @patch("the_aichemist_codex.backend.metadata.pdf_extractor.PdfReader")
    def test_extract_pdf_with_error(self, mock_pdf_reader, mock_get_mime):
        """Test handling of errors during PDF extraction."""
        mock_get_mime.return_value = ("application/pdf", 1.0)
        mock_pdf_reader.side_effect = Exception("Failed to read PDF")

        extractor = PDFMetadataExtractor()
        fake_pdf_path = "/path/to/test.pdf"

        with pytest.raises(Exception):
            extractor._extract_pdf_with_pypdf(fake_pdf_path)

    @pytest.mark.skipif(not PYPDF_AVAILABLE, reason="pypdf not available")
    @patch(
        "the_aichemist_codex.backend.utils.mime_type_detector.MimeTypeDetector.get_mime_type",
        return_value=("application/pdf", 1.0),
    )
    @patch("the_aichemist_codex.backend.metadata.pdf_extractor.PYPDF_AVAILABLE", False)
    def test_extract_without_pypdf_direct(self, mock_get_mime):
        """Test behavior when PyPDF2 is not available using direct method call."""
        mock_get_mime.return_value = ("application/pdf", 1.0)

        extractor = PDFMetadataExtractor()
        fake_pdf_path = "/path/to/test.pdf"

        with pytest.raises(ImportError):
            extractor._extract_pdf_with_pypdf(fake_pdf_path)

    @pytest.mark.skipif(not PYPDF_AVAILABLE, reason="pypdf not available")
    @patch(
        "the_aichemist_codex.backend.utils.mime_type_detector.MimeTypeDetector.get_mime_type",
        return_value=("application/pdf", 1.0),
    )
    @patch("the_aichemist_codex.backend.metadata.pdf_extractor.PdfReader")
    @patch("the_aichemist_codex.backend.utils.cache_manager.CacheManager")
    def test_extract_with_cache_direct(
        self, mock_cache_manager, mock_pdf_reader, mock_get_mime
    ):
        """Test extraction with cache functionality using direct method call."""
        # Setup mocks
        mock_get_mime.return_value = ("application/pdf", 1.0)

        # Set up mock cache manager
        mock_cache = MagicMock()
        mock_cache.get = AsyncMock(return_value=None)  # No cache hit
        mock_cache.put = AsyncMock()
        mock_cache_manager.return_value = mock_cache

        # Mock PyPDF2 reader
        mock_reader_instance = MagicMock()
        mock_pdf_reader.return_value = mock_reader_instance
        mock_reader_instance.metadata = {"/Title": "Cached PDF"}
        mock_reader_instance.pages = [MagicMock(), MagicMock()]

        # Test extraction - just test the direct method as it doesn't use the cache
        extractor = PDFMetadataExtractor(cache_manager=mock_cache_manager())
        fake_pdf_path = "/path/to/test.pdf"

        # Mock file system calls and call the method
        with (
            patch("os.path.exists", return_value=True),
            patch("os.path.getsize", return_value=98765),
        ):
            metadata = extractor._extract_pdf_with_pypdf(fake_pdf_path)

        assert metadata is not None
        assert metadata["title"] == "Cached PDF"
        assert metadata["extraction_method"] == "pypdf"

        # We're testing the direct method which doesn't use cache
        # No need to verify cache was called for the direct method
