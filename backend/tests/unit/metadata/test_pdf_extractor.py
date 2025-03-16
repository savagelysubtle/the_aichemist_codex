"""Tests for the PDF metadata extractor module.

This module contains unit tests for the PDFMetadataExtractor class.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from backend.src.metadata.pdf_extractor import PYPDF2_AVAILABLE, PDFMetadataExtractor


@pytest.fixture
def pdf_extractor():
    """Fixture for creating a PDF extractor instance."""
    return PDFMetadataExtractor()


@pytest.mark.skipif(not PYPDF2_AVAILABLE, reason="PyPDF2 is not installed")
class TestPDFMetadataExtractor:
    """Test suite for the PDF metadata extractor."""

    @pytest.mark.metadata
@pytest.mark.unit
def test_supported_mime_types(self, pdf_extractor):
        """Test the supported MIME types."""
        assert "application/pdf" in pdf_extractor.supported_mime_types
        assert len(pdf_extractor.supported_mime_types) >= 1

    @pytest.mark.metadata
@pytest.mark.unit
@pytest.mark.asyncio
async def test_file_extensions(self, pdf_extractor):
        """Test the file extension mapping."""
        assert ".pdf" in pdf_extractor.FILE_EXTENSIONS
        assert pdf_extractor.FILE_EXTENSIONS[".pdf"] == "application/pdf"

    @pytest.mark.asyncio
@pytest.mark.metadata
@pytest.mark.unit
async def test_extract_nonexistent_file(self, pdf_extractor):
        """Test extraction with a nonexistent file."""
        with pytest.raises(FileNotFoundError):
            await pdf_extractor.extract("/nonexistent/file.pdf")

    @pytest.mark.asyncio
@pytest.mark.metadata
@pytest.mark.unit
async def test_extract_unsupported_mime_type(self, pdf_extractor):
        """Test extraction with an unsupported MIME type."""
        # Create a temporary file
        tmp_file = Path("test_file.txt")
        tmp_file.write_text("This is not a PDF file")

        try:
            # Mock the MIME type detector to return an unsupported type
            with patch.object(
                pdf_extractor.mime_detector, "get_mime_type", return_value="text/plain"
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
async def test_extract_with_cache(self, pdf_extractor):
        """Test extraction with cache."""
        # Set up mocks
        cache_manager = MagicMock()
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
            with patch.object(
                pdf_extractor.mime_detector,
                "get_mime_type",
                return_value="application/pdf",
            ):
                result = await pdf_extractor.extract(file_path)

                assert result == cached_data
                cache_manager.get.assert_called_once()
                cache_manager.put.assert_not_called()
        finally:
            # Clean up
            if file_path.exists():
                file_path.unlink()

    @pytest.mark.asyncio
@pytest.mark.metadata
@pytest.mark.unit
async def test_extract_without_pypdf(self, pdf_extractor):
        """Test extraction when PyPDF2 is not available."""
        with patch("backend.src.metadata.pdf_extractor.PYPDF2_AVAILABLE", False):
            # Create a temporary file
            tmp_file = Path("test_file.pdf")
            tmp_file.write_text("This is a fake PDF file")

            try:
                # Mock the MIME type detector to return a supported type
                with patch.object(
                    pdf_extractor.mime_detector,
                    "get_mime_type",
                    return_value="application/pdf",
                ):
                    result = await pdf_extractor.extract(tmp_file)
                    assert result["metadata_type"] == "pdf"
                    assert "error" in result
                    assert "PyPDF2 is required" in result["error"]
            finally:
                # Clean up
                if tmp_file.exists():
                    tmp_file.unlink()

    @pytest.mark.asyncio
@pytest.mark.metadata
@pytest.mark.unit
async def test_extract_with_pypdf_error(self, pdf_extractor):
        """Test extraction when PyPDF2 raises an error."""
        # Create a temporary file
        tmp_file = Path("test_file.pdf")
        tmp_file.write_text("This is a fake PDF file that will cause PyPDF2 to error")

        try:
            # Mock the MIME type detector to return a supported type
            with patch.object(
                pdf_extractor.mime_detector,
                "get_mime_type",
                return_value="application/pdf",
            ):
                # Mock PyPDF2 to raise an error
                with patch.object(
                    pdf_extractor,
                    "_extract_pdf_with_pypdf",
                    side_effect=Exception("PyPDF2 error"),
                ):
                    result = await pdf_extractor.extract(tmp_file)
                    assert result["metadata_type"] == "pdf"
                    assert "error" in result
                    assert "PyPDF2 error" in result["error"]
        finally:
            # Clean up
            if tmp_file.exists():
                tmp_file.unlink()

    def test_extract_with_pypdf(self, pdf_extractor):
        """Test the PyPDF2 extraction method directly."""
        # This test would require a real PDF file
        # For unit testing purposes, we'll mock PdfReader instead

        with patch("backend.src.metadata.pdf_extractor.PdfReader") as mock_reader:
            # Set up the mock
            mock_pdf = MagicMock()
            mock_reader.return_value = mock_pdf

            # Mock properties and methods
            mock_pdf.metadata = {"/Title": "Test PDF", "/Author": "Test Author"}
            mock_pdf.is_encrypted = False
            mock_pdf.pages = [MagicMock(), MagicMock()]  # Two pages

            # Mock page properties
            page0 = mock_pdf.pages[0]
            page0.get.return_value = 0  # Rotation
            page0.mediabox.width = 612.0
            page0.mediabox.height = 792.0
            page0.extract_text.return_value = "Page 1 content"

            page1 = mock_pdf.pages[1]
            page1.get.return_value = 0  # Rotation
            page1.mediabox.width = 612.0
            page1.mediabox.height = 792.0
            page1.extract_text.return_value = "Page 2 content"

            # Create a temporary file path
            file_path = "test_file.pdf"

            # Call the method
            result = pdf_extractor._extract_pdf_with_pypdf(file_path)

            # Assert the results
            assert result["metadata_type"] == "pdf"
            assert result["document_info"]["Title"] == "Test PDF"
            assert result["document_info"]["Author"] == "Test Author"
            assert result["structure"]["page_count"] == 2
            assert len(result["structure"]["pages"]) == 2
            assert result["structure"]["pages"][0]["page_number"] == 1
            assert result["structure"]["pages"][0]["width"] == 612.0
            assert result["structure"]["pages"][0]["height"] == 792.0
            assert result["structure"]["pages"][0]["text_length"] == len(
                "Page 1 content"
            )
            assert result["structure"]["pages"][0]["has_text"] is True
            assert result["security"]["encrypted"] is False
