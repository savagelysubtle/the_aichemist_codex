"""
Unit tests for the PDF metadata extractor.

These tests verify the functionality of the PDFMetadataExtractor class,
ensuring it correctly extracts metadata from PDF files.
"""

from pathlib import Path
from unittest import mock

import pytest
from PyPDF2.errors import PdfReadError

from backend.src.metadata.pdf_extractor import PDFMetadataExtractor


@pytest.fixture
def pdf_extractor():
    """Create a PDF metadata extractor instance for testing."""
    return PDFMetadataExtractor()


def test_supported_mime_types(pdf_extractor):
    """Test the supported_mime_types property returns the correct MIME types."""
    mime_types = pdf_extractor.supported_mime_types

    # Verify that the expected MIME types are supported
    assert "application/pdf" in mime_types
    assert "application/x-pdf" in mime_types
    assert "application/acrobat" in mime_types
    assert "application/vnd.pdf" in mime_types
    assert len(mime_types) == 4


@mock.patch("backend.src.metadata.pdf_extractor.PdfReader")
async def test_extract_nonexistent_file(mock_pdfreader, pdf_extractor):
    """Test extraction with a non-existent file."""
    # Set up a non-existent file path
    nonexistent_path = Path("/path/to/nonexistent/file.pdf")

    # Mock the Path.exists method to return False
    with mock.patch("pathlib.Path.exists", return_value=False):
        result = await pdf_extractor.extract(nonexistent_path)

    # Verify that an empty dict is returned for non-existent files
    assert result == {}
    # Ensure PdfReader was not called
    mock_pdfreader.assert_not_called()


@mock.patch("backend.src.metadata.pdf_extractor.PdfReader")
async def test_extract_unsupported_mime_type(mock_pdfreader, pdf_extractor):
    """Test extraction with an unsupported MIME type."""
    # Set up a test file path
    test_path = Path("/path/to/test/file.txt")

    # Mock Path.exists to return True
    with mock.patch("pathlib.Path.exists", return_value=True):
        # Mock the mime_detector.get_mime_type to return an unsupported MIME type
        with mock.patch.object(
            pdf_extractor.mime_detector,
            "get_mime_type",
            return_value=("text/plain", None),
        ):
            result = await pdf_extractor.extract(test_path)

    # Verify that an empty dict is returned for unsupported MIME types
    assert result == {}
    # Ensure PdfReader was not called
    mock_pdfreader.assert_not_called()


@mock.patch("backend.src.utils.cache_manager.CacheManager")
async def test_cache_usage(mock_cache_manager, pdf_extractor):
    """Test that caching is properly used when a cache manager is provided."""
    # Create a PDF extractor with a mocked cache manager
    cache_manager = mock.MagicMock()
    cache_manager.get = mock.AsyncMock(
        return_value={"metadata_type": "pdf", "cached": True}
    )
    pdf_extractor_with_cache = PDFMetadataExtractor(cache_manager=cache_manager)

    # Set up test path and mock data
    test_path = Path("/path/to/test/file.pdf")
    cached_data = {"metadata_type": "pdf", "cached": True}

    # Mock Path.exists and stat
    with mock.patch("pathlib.Path.exists", return_value=True):
        with mock.patch("pathlib.Path.stat") as mock_stat:
            # Set up the mock stat result
            mock_stat_result = mock.MagicMock()
            mock_stat_result.st_mtime = 12345
            mock_stat.return_value = mock_stat_result

            # Mock the mime_detector to return a supported MIME type
            with mock.patch.object(
                pdf_extractor_with_cache.mime_detector,
                "get_mime_type",
                return_value=("application/pdf", None),
            ):
                # Call extract
                result = await pdf_extractor_with_cache.extract(test_path)

                # Verify cache key and result
                cache_manager.get.assert_called_once()
                assert result == cached_data


@mock.patch("backend.src.metadata.pdf_extractor.open", create=True)
@mock.patch("backend.src.metadata.pdf_extractor.PdfReader")
async def test_extract_error_handling(mock_pdfreader, mock_open, pdf_extractor):
    """Test error handling when processing a PDF file."""
    # Set up a test file path
    test_path = Path("/path/to/test/file.pdf")

    # Mock Path.exists to return True
    with mock.patch("pathlib.Path.exists", return_value=True):
        # Mock stat
        with mock.patch("pathlib.Path.stat") as mock_stat:
            # Set up the mock stat result
            mock_stat_result = mock.MagicMock()
            mock_stat_result.st_size = 1024  # 1KB
            mock_stat.return_value = mock_stat_result

            # Mock the mime_detector to return a supported MIME type
            with mock.patch.object(
                pdf_extractor.mime_detector,
                "get_mime_type",
                return_value=("application/pdf", None),
            ):
                # Set up PdfReader to raise an exception
                mock_pdfreader.side_effect = PdfReadError("Invalid PDF file")

                # Call extract
                result = await pdf_extractor.extract(test_path)

                # Verify error handling
                assert result["metadata_type"] == "pdf"
                assert "error" in result
                assert "Error extracting PDF metadata" in result["error"]


@mock.patch("backend.src.metadata.pdf_extractor.open", create=True)
async def test_process_pdf_basic_info(mock_open, pdf_extractor):
    """Test processing a PDF file with basic information."""
    # Set up a test file path
    test_path = Path("/path/to/test/file.pdf")

    # Mock Path.exists to return True and set file size
    with mock.patch("pathlib.Path.exists", return_value=True):
        with mock.patch("pathlib.Path.stat") as mock_stat:
            # Set up the mock stat result
            mock_stat_result = mock.MagicMock()
            mock_stat_result.st_size = 1024  # 1KB
            mock_stat.return_value = mock_stat_result

            # Create a mock PDF reader instance
            mock_reader = mock.MagicMock()

            # Set up basic PDF properties
            mock_reader.metadata = {
                "/Title": "Test Document",
                "/Author": "Test Author",
                "/CreationDate": "D:20230101120000",
                "/Producer": "Test Producer",
            }

            # Set up page information
            mock_page = mock.MagicMock()
            mock_page.mediabox.width = 612  # Letter width in points
            mock_page.mediabox.height = 792  # Letter height in points
            mock_page.extract_text.return_value = "This is test content"
            mock_page.get.return_value = 0  # No rotation

            # Set up resources for font detection
            mock_resources = {
                "/Font": {
                    "/F1": {"/BaseFont": "/Arial"},
                    "/F2": {"/BaseFont": "/TimesNewRoman"},
                }
            }

            # Mock page dictionary access for resources
            mock_page.get.side_effect = (
                lambda key, default=None: mock_resources
                if key == "/Resources"
                else default
            )

            # Set up resources for image detection
            mock_image_resources = {
                "/XObject": {
                    "/Im1": {"/Subtype": "/Image"},
                    "/Im2": {"/Subtype": "/Image"},
                }
            }

            # Add resources method to page
            def get_item(key):
                if key == "/Resources":
                    return mock_resources
                return {}

            mock_page.__getitem__ = get_item

            # Set up pages
            mock_reader.pages = [mock_page]

            # Set up PDF header
            mock_reader.pdf_header = "PDF-1.7"

            # Set up security information
            mock_reader.is_encrypted = False

            # Mock PyPDF2.PdfReader to return our mock
            with mock.patch(
                "backend.src.metadata.pdf_extractor.PdfReader", return_value=mock_reader
            ):
                # Call _process_pdf directly to test its functionality
                result = await pdf_extractor._process_pdf(test_path)

                # Verify basic document info
                assert result["metadata_type"] == "pdf"
                assert result["document"]["file_size"] == 1024
                assert result["document"]["title"] == "Test Document"
                assert result["document"]["author"] == "Test Author"
                assert result["document"]["pdf_version"] == "PDF-1.7"

                # Verify structure info
                assert result["structure"]["page_count"] == 1

                # Verify summary
                assert (
                    "PDF document 'Test Document' by Test Author with 1 page"
                    in result["summary"]
                )


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
