"""
Unit tests for the video metadata extractor.

These tests verify the functionality of the VideoMetadataExtractor class,
ensuring it correctly extracts metadata from video files.
"""

from pathlib import Path
from unittest import mock

import pytest

from the_aichemist_codex.backend.metadata.video_extractor import VideoMetadataExtractor


@pytest.fixture
def video_extractor():
    """Create a video metadata extractor instance for testing."""
    return VideoMetadataExtractor()


@pytest.mark.metadata
@pytest.mark.unit
def test_supported_mime_types(video_extractor):
    """Test the supported_mime_types property returns the correct MIME types."""
    mime_types = video_extractor.supported_mime_types

    # Verify that expected MIME types are supported
    assert "video/mp4" in mime_types
    assert "video/x-msvideo" in mime_types  # AVI
    assert "video/x-matroska" in mime_types  # MKV
    assert "video/quicktime" in mime_types  # MOV
    assert len(mime_types) > 5  # Should have multiple formats supported


@pytest.mark.metadata
@pytest.mark.unit
@pytest.mark.asyncio
async def test_extension_mapping(video_extractor):
    """Test that file extension mapping contains expected entries."""
    # Access the extension mapping directly from the class
    mapping = VideoMetadataExtractor.EXTENSION_MAPPING

    # Verify some common extensions are mapped correctly
    assert mapping[".mp4"] == "video/mp4"
    assert mapping[".avi"] == "video/x-msvideo"
    assert mapping[".mkv"] == "video/x-matroska"
    assert mapping[".mov"] == "video/quicktime"


@mock.patch(
    "the_aichemist_codex.backend.metadata.video_extractor.MediaInfo", autospec=True
)
@pytest.mark.asyncio
@pytest.mark.metadata
@pytest.mark.unit
async def test_extract_nonexistent_file(mock_mediainfo, video_extractor):
    """Test extraction of metadata from a nonexistent file."""
    # Mock the get_mime_type method to avoid detection attempt
    with mock.patch(
        "the_aichemist_codex.backend.utils.mime_type_detector.MimeTypeDetector.get_mime_type",
        return_value=("video/mp4", 1.0),
    ):
        # Test with a clearly nonexistent path
        with mock.patch("pathlib.Path.exists", return_value=False):
            result = await video_extractor.extract("/this/path/does/not/exist.mp4")

        # The extractor should return an empty dict for nonexistent files
        assert result == {}

        # Verify that the MediaInfo object was not instantiated
        mock_mediainfo.assert_not_called()


@mock.patch(
    "the_aichemist_codex.backend.metadata.video_extractor.MediaInfo", autospec=True
)
@pytest.mark.asyncio
@pytest.mark.metadata
@pytest.mark.unit
async def test_extract_unsupported_mime_type(mock_mediainfo, video_extractor):
    """Test extraction with an unsupported MIME type."""
    # Create a temporary file
    tmp_file = Path("test_file.txt")
    tmp_file.write_text("This is not a video file")

    try:
        # Mock the MIME type detector to return an unsupported type
        with mock.patch(
            "the_aichemist_codex.backend.utils.mime_type_detector.MimeTypeDetector.get_mime_type",
            return_value=("text/plain", 1.0),
        ):
            result = await video_extractor.extract(tmp_file)

        # The extractor should return an empty dict for unsupported MIME types
        assert result == {}

        # Verify MediaInfo was not used
        mock_mediainfo.assert_not_called()
    finally:
        # Clean up
        if tmp_file.exists():
            tmp_file.unlink()


@mock.patch("the_aichemist_codex.backend.utils.cache_manager.CacheManager")
@pytest.mark.asyncio
@pytest.mark.metadata
@pytest.mark.unit
async def test_cache_usage(mock_cache_manager, video_extractor):
    """Test that the cache is properly used."""
    # Set up the cache mock
    mock_cache = mock.MagicMock()
    mock_cache.get = mock.AsyncMock(return_value=None)  # No cache hit initially
    mock_cache.put = mock.AsyncMock()
    mock_cache_manager.return_value = mock_cache

    # Add the cache manager to the extractor
    video_extractor.cache_manager = mock_cache_manager()

    # Create a temp video file
    test_file = Path("test_video.mp4")
    test_file.write_text("Mock video content")

    try:
        # Mock MIME type detection to return a supported type
        with mock.patch(
            "the_aichemist_codex.backend.utils.mime_type_detector.MimeTypeDetector.get_mime_type",
            return_value=("video/mp4", 1.0),
        ):
            # Mock a successful extraction using the _extract_with_mediainfo method
            with mock.patch.object(
                video_extractor,
                "_extract_with_mediainfo",
                return_value={"metadata_type": "video", "test": "data"},
            ):
                await video_extractor.extract(test_file)

        # The cache should have been checked and the result stored
        mock_cache.get.assert_called_once()
        mock_cache.put.assert_called_once()
    finally:
        if test_file.exists():
            test_file.unlink()


@mock.patch(
    "the_aichemist_codex.backend.metadata.video_extractor.MEDIAINFO_AVAILABLE", False
)
@mock.patch(
    "the_aichemist_codex.backend.metadata.video_extractor.FFMPEG_AVAILABLE", False
)
@pytest.mark.asyncio
@pytest.mark.metadata
@pytest.mark.unit
async def test_extract_no_available_methods(video_extractor):
    """Test extraction when no processing methods are available."""
    test_file = Path("test_video.mp4")
    test_file.write_text("Mock video content")

    try:
        with mock.patch(
            "the_aichemist_codex.backend.utils.mime_type_detector.MimeTypeDetector.get_mime_type",
            return_value=("video/mp4", 1.0),
        ):
            result = await video_extractor.extract(test_file)

        # Should return basic metadata with an error message
        assert result["metadata_type"] == "video"
        assert "error" in result
        assert "Could not extract detailed metadata" in result["error"]
    finally:
        if test_file.exists():
            test_file.unlink()


@mock.patch(
    "the_aichemist_codex.backend.metadata.video_extractor.MEDIAINFO_AVAILABLE", True
)
@mock.patch("the_aichemist_codex.backend.metadata.video_extractor.MediaInfo.parse")
@pytest.mark.asyncio
@pytest.mark.metadata
@pytest.mark.unit
async def test_extract_with_mediainfo(mock_parse, video_extractor):
    """Test extraction using MediaInfo."""
    # Create the test file
    test_file = Path("test_video.mp4")
    test_file.write_text("Mock video content")

    try:
        # Set up the mock to return video metadata
        mock_media_info = mock.MagicMock()
        mock_parse.return_value = mock_media_info

        # Create mock tracks
        mock_general_track = mock.MagicMock()
        mock_general_track.to_dict.return_value = {
            "format": "MPEG-4",
            "duration": "60000",
            "overall_bit_rate": "5000000",
        }

        mock_video_track = mock.MagicMock()
        mock_video_track.to_dict.return_value = {
            "format": "AVC",
            "width": 1920,
            "height": 1080,
            "duration": "60000",
            "bit_rate": "5000000",
        }

        mock_audio_track = mock.MagicMock()
        mock_audio_track.to_dict.return_value = {
            "format": "AAC",
            "channel_s": 2,
            "sampling_rate": 48000,
            "bit_rate": "192000",
        }

        # Set up the tracks on the mock MediaInfo result
        mock_media_info.general_tracks = [mock_general_track]
        mock_media_info.video_tracks = [mock_video_track]
        mock_media_info.audio_tracks = [mock_audio_track]
        mock_media_info.text_tracks = []
        mock_media_info.menu_tracks = []

        # Mock the MIME type detection
        with mock.patch(
            "the_aichemist_codex.backend.utils.mime_type_detector.MimeTypeDetector.get_mime_type",
            return_value=("video/mp4", 1.0),
        ):
            # Mock Path.exists and Path.stat to avoid file system operations
            with mock.patch("pathlib.Path.exists", return_value=True):
                with mock.patch("pathlib.Path.stat") as mock_stat:
                    mock_stat_result = mock.MagicMock()
                    mock_stat_result.st_size = 1000000
                    mock_stat_result.st_mtime = 123456789
                    mock_stat.return_value = mock_stat_result

                    # Call the extract method
                    result = await video_extractor.extract(test_file)

        # Verify MediaInfo.parse was called correctly
        mock_parse.assert_called_once_with(test_file)

        # Check result structure
        assert result["metadata_type"] == "video"
        assert "container" in result
        assert "video_streams" in result
        assert "audio_streams" in result
        assert result["extraction_method"] == "mediainfo"
    finally:
        # Clean up
        if test_file.exists():
            test_file.unlink()


@pytest.mark.metadata
@pytest.mark.unit
def test_parse_bitrate():
    """Test the _parse_bitrate helper method."""
    video_extractor = VideoMetadataExtractor()

    # Test with integer string
    assert video_extractor._parse_bitrate("1000") == 1000

    # Test with integer converted to string
    assert video_extractor._parse_bitrate(str(2000)) == 2000

    # Test with string containing non-numeric characters
    assert video_extractor._parse_bitrate("1500 bps") == 1500

    # Test with empty string
    assert video_extractor._parse_bitrate("") == 0

    # Test with None converted to empty string
    assert video_extractor._parse_bitrate("") == 0  # Simulating None behavior


@pytest.mark.metadata
@pytest.mark.unit
def test_format_duration():
    """Test the _format_duration helper method."""
    video_extractor = VideoMetadataExtractor()

    # Test with seconds less than a minute
    assert video_extractor._format_duration(45) == "00:45"

    # Test with minutes and seconds
    assert video_extractor._format_duration(125) == "02:05"

    # Test with hours, minutes, and seconds
    assert video_extractor._format_duration(3665) == "01:01:05"

    # Test with zero
    assert video_extractor._format_duration(0) == "00:00"


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
