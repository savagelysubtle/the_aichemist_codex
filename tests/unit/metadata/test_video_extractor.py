"""
Unit tests for the video metadata extractor.

These tests verify the functionality of the VideoMetadataExtractor class,
ensuring it correctly extracts metadata from video files.
"""

from pathlib import Path
from unittest import mock

import pytest

from backend.src.metadata.video_extractor import VideoMetadataExtractor


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


@mock.patch("backend.src.metadata.video_extractor.MediaInfo", autospec=True)
@pytest.mark.asyncio
@pytest.mark.metadata
@pytest.mark.unit
async def test_extract_nonexistent_file(mock_mediainfo, video_extractor):
    """Test extraction with a non-existent file."""
    # Set up a non-existent file path
    nonexistent_path = Path("/path/to/nonexistent/video.mp4")

    # Mock the Path.exists method to return False
    with mock.patch("pathlib.Path.exists", return_value=False):
        result = await video_extractor.extract(nonexistent_path)

    # Verify that an empty dict is returned for non-existent files
    assert result == {}
    # Ensure MediaInfo was not called
    mock_mediainfo.parse.assert_not_called()


@mock.patch("backend.src.metadata.video_extractor.MediaInfo", autospec=True)
@pytest.mark.asyncio
@pytest.mark.metadata
@pytest.mark.unit
async def test_extract_unsupported_mime_type(mock_mediainfo, video_extractor):
    """Test extraction with an unsupported MIME type."""
    # Set up a test file path
    test_path = Path("/path/to/test/file.txt")

    # Mock Path.exists to return True
    with mock.patch("pathlib.Path.exists", return_value=True):
        # Mock the mime_detector.get_mime_type to return an unsupported MIME type
        with mock.patch.object(
            video_extractor.mime_detector,
            "get_mime_type",
            return_value=("text/plain", None),
        ):
            result = await video_extractor.extract(test_path)

    # Verify that an empty dict is returned for unsupported MIME types
    assert result == {}
    # Ensure MediaInfo was not called
    mock_mediainfo.parse.assert_not_called()


@mock.patch("backend.src.utils.cache_manager.CacheManager")
@pytest.mark.asyncio
@pytest.mark.metadata
@pytest.mark.unit
async def test_cache_usage(mock_cache_manager, video_extractor):
    """Test that caching is properly used when a cache manager is provided."""
    # Create a video extractor with a mocked cache manager
    cache_manager = mock.MagicMock()
    cache_manager.get = mock.AsyncMock(
        return_value={"metadata_type": "video", "cached": True}
    )
    video_extractor_with_cache = VideoMetadataExtractor(cache_manager=cache_manager)

    # Set up test path and mock data
    test_path = Path("/path/to/test/video.mp4")
    cached_data = {"metadata_type": "video", "cached": True}

    # Mock Path.exists and stat
    with mock.patch("pathlib.Path.exists", return_value=True):
        with mock.patch("pathlib.Path.stat") as mock_stat:
            # Set up the mock stat result
            mock_stat_result = mock.MagicMock()
            mock_stat_result.st_mtime = 12345
            mock_stat.return_value = mock_stat_result

            # Mock the mime_detector to return a supported MIME type
            with mock.patch.object(
                video_extractor_with_cache.mime_detector,
                "get_mime_type",
                return_value=("video/mp4", None),
            ):
                # Call extract
                result = await video_extractor_with_cache.extract(test_path)

                # Verify cache key and result
                cache_manager.get.assert_called_once()
                assert result == cached_data


@mock.patch("backend.src.metadata.video_extractor.MEDIAINFO_AVAILABLE", False)
@mock.patch("backend.src.metadata.video_extractor.FFMPEG_AVAILABLE", False)
@pytest.mark.asyncio
@pytest.mark.metadata
@pytest.mark.unit
async def test_extract_no_available_methods(video_extractor):
    """Test extraction when no extraction methods are available."""
    # Set up a test file path
    test_path = Path("/path/to/test/video.mp4")

    # Mock Path.exists and stat
    with mock.patch("pathlib.Path.exists", return_value=True):
        with mock.patch("pathlib.Path.stat") as mock_stat:
            # Set up the mock stat result
            mock_stat_result = mock.MagicMock()
            mock_stat_result.st_size = 1024  # 1KB
            mock_stat.return_value = mock_stat_result

            # Mock the mime_detector to return a supported MIME type
            with mock.patch.object(
                video_extractor.mime_detector,
                "get_mime_type",
                return_value=("video/mp4", None),
            ):
                # Call extract
                result = await video_extractor.extract(test_path)

                # Verify basic information is still extracted
                assert result["metadata_type"] == "video"
                assert "container" in result
                assert result["container"]["file_size"] == 1024
                assert "error" in result  # Should have an error message


@mock.patch("backend.src.metadata.video_extractor.MEDIAINFO_AVAILABLE", True)
@mock.patch("backend.src.metadata.video_extractor.MediaInfo")
@pytest.mark.asyncio
@pytest.mark.metadata
@pytest.mark.unit
async def test_extract_with_mediainfo(mock_mediainfo, video_extractor):
    """Test video extraction using MediaInfo."""
    # Set up a test file path
    test_path = Path("/path/to/test/video.mp4")

    # Create mock MediaInfo
    mock_media_info = mock.MagicMock()
    mock_mediainfo.parse.return_value = mock_media_info

    # Create mock general track
    mock_general_track = mock.MagicMock()
    mock_general_track.to_dict.return_value = {
        "format": "MPEG-4",
        "duration": "60000",  # 60 seconds in ms
        "overall_bit_rate": "1000000",
        "tag_title": "Test Video",
        "tag_artist": "Test Artist",
    }
    mock_media_info.general_tracks = [mock_general_track]

    # Create mock video track
    mock_video_track = mock.MagicMock()
    mock_video_track.to_dict.return_value = {
        "track_id": 1,
        "format": "AVC",
        "codec": "H.264",
        "width": 1920,
        "height": 1080,
        "frame_rate": "30",
        "bit_rate": "800000",
        "duration": "60000",
    }
    mock_media_info.video_tracks = [mock_video_track]

    # Create mock audio track
    mock_audio_track = mock.MagicMock()
    mock_audio_track.to_dict.return_value = {
        "track_id": 2,
        "format": "AAC",
        "codec": "AAC LC",
        "channel_s": 2,
        "sampling_rate": 48000,
        "bit_rate": "192000",
        "duration": "60000",
    }
    mock_media_info.audio_tracks = [mock_audio_track]

    # Create empty lists for other tracks
    mock_media_info.text_tracks = []
    mock_media_info.menu_tracks = []

    # Mock Path.exists and stat
    with mock.patch("pathlib.Path.exists", return_value=True):
        with mock.patch("pathlib.Path.stat") as mock_stat:
            # Set up the mock stat result
            mock_stat_result = mock.MagicMock()
            mock_stat_result.st_size = 7654321  # ~7.6MB
            mock_stat.return_value = mock_stat_result

            # Mock the mime_detector to return a supported MIME type
            with mock.patch.object(
                video_extractor.mime_detector,
                "get_mime_type",
                return_value=("video/mp4", None),
            ):
                # Call extract
                result = await video_extractor.extract(test_path)

                # Verify MediaInfo was called
                mock_mediainfo.parse.assert_called_once_with(test_path)

                # Verify result structure
                assert result["metadata_type"] == "video"
                assert result["extraction_method"] == "mediainfo"

                # Verify container info
                assert result["container"]["format"] == "MPEG-4"
                assert result["container"]["duration_seconds"] == 60.0
                assert result["container"]["bitrate"] == 1000000

                # Verify video stream info
                assert len(result["video_streams"]) == 1
                assert result["video_streams"][0]["codec"] == "H.264"
                assert result["video_streams"][0]["width"] == 1920
                assert result["video_streams"][0]["height"] == 1080
                assert result["video_streams"][0]["resolution"] == "1920x1080"
                assert result["video_streams"][0]["frame_rate"] == 30.0

                # Verify audio stream info
                assert len(result["audio_streams"]) == 1
                assert result["audio_streams"][0]["codec"] == "AAC LC"
                assert result["audio_streams"][0]["channels"] == 2
                assert result["audio_streams"][0]["sample_rate"] == 48000

                # Verify tags
                assert result["tags"]["title"] == "Test Video"
                assert result["tags"]["artist"] == "Test Artist"

                # Verify summary
                assert "Video:" in result["summary"]
                assert "1920x1080" in result["summary"]
                assert "01:00" in result["summary"] or "1m" in result["summary"]


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
