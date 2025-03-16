"""
Video metadata extraction for The Aichemist Codex.

This module provides functionality to extract metadata from video files,
including format information, codec details, duration, resolution, frame rate,
and other video-specific metadata.
"""

import logging
from pathlib import Path
from typing import Any, Protocol, cast

# Local application imports
from backend.src.file_reader.file_metadata import FileMetadata
from backend.src.metadata.extractor import (
    BaseMetadataExtractor,
    MetadataExtractorRegistry,
)
from backend.src.utils.cache_manager import CacheManager
from backend.src.utils.mime_type_detector import MimeTypeDetector

# Initialize logger with proper name
logger = logging.getLogger(__name__)

# Third-party imports
try:
    from pymediainfo import MediaInfo

    MEDIAINFO_AVAILABLE = True
except ImportError:
    MEDIAINFO_AVAILABLE = False

# Import ffmpeg-python library for video analysis
# The actual module name is 'ffmpeg' but it has a function called 'probe'
FFMPEG_AVAILABLE = False
try:
    import ffmpeg

    # Check if probe function exists in the ffmpeg module
    if hasattr(ffmpeg, "probe"):
        FFMPEG_AVAILABLE = True
    else:
        logger.warning("ffmpeg module found but 'probe' function is not available")
except ImportError:
    pass


# Define a protocol for what we expect from ffmpeg
class FFmpegWithProbe(Protocol):
    def probe(self, path: str) -> dict[str, Any]: ...


class VideoMetadataExtractor(BaseMetadataExtractor):
    """
    Metadata extractor for video files.

    This extractor can process video files and extract rich metadata including:
    - Format information (container, size, bitrate)
    - Video track details (codec, resolution, frame rate)
    - Audio track details (codec, channels, sample rate)
    - Duration and timestamps
    - Metadata tags (title, artist, etc.)
    - Stream information for multi-track videos
    """

    # Supported MIME types
    SUPPORTED_MIME_TYPES = [
        "video/mp4",
        "video/x-msvideo",  # AVI
        "video/x-matroska",  # MKV
        "video/quicktime",  # MOV
        "video/x-ms-wmv",  # WMV
        "video/webm",  # WebM
        "video/x-flv",  # FLV
        "video/mpeg",  # MPEG
        "video/3gpp",  # 3GP
        "video/3gpp2",  # 3G2
        "video/ogg",  # OGV
    ]

    # File extensions mapping (for cases where MIME type detection fails)
    EXTENSION_MAPPING = {
        ".mp4": "video/mp4",
        ".avi": "video/x-msvideo",
        ".mkv": "video/x-matroska",
        ".mov": "video/quicktime",
        ".wmv": "video/x-ms-wmv",
        ".webm": "video/webm",
        ".flv": "video/x-flv",
        ".mpeg": "video/mpeg",
        ".mpg": "video/mpeg",
        ".3gp": "video/3gpp",
        ".3g2": "video/3gpp2",
        ".ogv": "video/ogg",
    }

    @property
    def supported_mime_types(self) -> list[str]:
        """Get the list of MIME types this extractor supports.

        Returns:
            List of supported MIME types
        """
        return self.SUPPORTED_MIME_TYPES

    def __init__(self, cache_manager: CacheManager | None = None) -> None:
        """Initialize the video metadata extractor.

        Args:
            cache_manager: Optional cache manager for caching extraction results
        """
        super().__init__(cache_manager)
        self.mime_detector = MimeTypeDetector()

        # Check if required libraries are available
        if not MEDIAINFO_AVAILABLE and not FFMPEG_AVAILABLE:
            logger.warning(
                "Neither pymediainfo nor ffmpeg are available. "
                "Video metadata extraction will be limited."
            )

    async def extract(
        self,
        file_path: str | Path,
        content: str | None = None,
        mime_type: str | None = None,
        metadata: FileMetadata | None = None,
    ) -> dict[str, Any]:
        """Extract metadata from a video file.

        Args:
            file_path: Path to the video file
            content: Not used for video files
            mime_type: Optional MIME type of the file
            metadata: Optional existing metadata to enhance

        Returns:
            Dictionary containing extracted video metadata
        """
        path = Path(file_path)
        if not path.exists():
            logger.warning(f"Video file not found: {path}")
            return {}

        # Determine MIME type if not provided
        if mime_type is None:
            mime_type, _ = self.mime_detector.get_mime_type(path)

            # Fall back to extension-based detection if needed
            if mime_type not in self.supported_mime_types:
                extension = path.suffix.lower()
                if extension in self.EXTENSION_MAPPING:
                    mime_type = self.EXTENSION_MAPPING[extension]

        # Check if this is a supported video type
        if mime_type not in self.supported_mime_types:
            logger.debug(
                f"Unsupported MIME type for video: {mime_type} for file: {path}"
            )
            return {}

        # Try to use cache if available
        if self.cache_manager:
            cache_key = f"video_metadata:{path}:{path.stat().st_mtime}"
            cached_data = await self.cache_manager.get(cache_key)
            if cached_data:
                logger.debug(f"Using cached video metadata for {path}")
                return cached_data

        # Process the video file
        try:
            result = await self._process_video(path)

            # Cache the result if cache manager is available
            if self.cache_manager:
                await self.cache_manager.put(cache_key, result)

            return result
        except Exception as e:
            logger.error(f"Error extracting video metadata from {path}: {str(e)}")
            return {
                "metadata_type": "video",
                "error": f"Error extracting video metadata: {str(e)}",
            }

    async def _process_video(self, path: Path) -> dict[str, Any]:
        """Process a video file to extract metadata.

        Args:
            path: Path to the video file

        Returns:
            Dictionary containing extracted video metadata
        """
        result = {
            "metadata_type": "video",
            "container": {},
            "video_streams": [],
            "audio_streams": [],
            "subtitle_streams": [],
            "other_streams": [],
            "chapters": [],
            "tags": {},
        }

        # Basic file information
        result["container"]["file_size"] = path.stat().st_size
        result["container"]["filename"] = path.name

        # First try MediaInfo if available (usually provides more detailed information)
        if MEDIAINFO_AVAILABLE:
            try:
                self._extract_with_mediainfo(path, result)

                # Successfully extracted with MediaInfo
                result["extraction_method"] = "mediainfo"
                return result
            except Exception as e:
                logger.warning(
                    f"MediaInfo extraction failed: {str(e)}. Trying ffmpeg..."
                )

        # Fall back to ffmpeg if MediaInfo failed or is not available
        if FFMPEG_AVAILABLE:
            try:
                self._extract_with_ffmpeg(path, result)

                # Successfully extracted with ffmpeg
                result["extraction_method"] = "ffmpeg"
                return result
            except Exception as e:
                logger.error(f"ffmpeg extraction failed: {str(e)}")

        # If we get here, both methods failed or were not available
        if not result.get("container", {}).get("format"):
            # Add minimal information from file stats if no extraction method worked
            result["container"]["format"] = "unknown"
            result["container"]["file_extension"] = path.suffix.lower()
            result["error"] = (
                "Could not extract detailed metadata with available methods"
            )

        # Create a summary
        if "duration_seconds" in result["container"]:
            mins, secs = divmod(int(result["container"]["duration_seconds"]), 60)
            hours, mins = divmod(mins, 60)

            if hours > 0:
                duration_str = f"{hours}h {mins}m {secs}s"
            else:
                duration_str = f"{mins}m {secs}s"

            result["summary"] = (
                f"Video: {result['container'].get('format', 'unknown format')}, "
                f"{duration_str}"
            )

            # Add resolution if available
            if result["video_streams"] and "resolution" in result["video_streams"][0]:
                result["summary"] += f", {result['video_streams'][0]['resolution']}"
        else:
            result["summary"] = f"Video file: {path.name}"

        return result

    def _extract_with_mediainfo(self, path: Path, result: dict[str, Any]) -> None:
        """Extract video metadata using MediaInfo.

        Args:
            path: Path to the video file
            result: Dictionary to update with extracted information
        """
        if not MEDIAINFO_AVAILABLE:
            raise ImportError("pymediainfo is not available")

        # Get MediaInfo data
        media_info = MediaInfo.parse(path)

        # Process general track (container info)
        for track in media_info.general_tracks:
            track_dict = track.to_dict()

            # Extract container format information
            result["container"]["format"] = track_dict.get("format", "unknown")

            # Extract duration
            if "duration" in track_dict:
                duration_ms = float(track_dict["duration"])
                result["container"]["duration_seconds"] = duration_ms / 1000
                result["container"]["duration_formatted"] = self._format_duration(
                    duration_ms / 1000
                )

            # Extract overall bitrate
            if "overall_bit_rate" in track_dict:
                result["container"]["bitrate"] = int(track_dict["overall_bit_rate"])

            # Extract container-level tags
            for key, value in track_dict.items():
                if key.startswith("tag_") and value:
                    tag_name = key[4:].lower()  # Remove "tag_" prefix
                    result["tags"][tag_name] = value

        # Process video tracks
        for track in media_info.video_tracks:
            track_dict = track.to_dict()
            video_stream = {
                "index": track_dict.get(
                    "stream_identifier", track_dict.get("track_id", 0)
                ),
                "codec": track_dict.get("codec", track_dict.get("format", "unknown")),
                "codec_profile": track_dict.get("format_profile", ""),
                "bitrate": self._parse_bitrate(track_dict.get("bit_rate", "0")),
            }

            # Resolution and aspect ratio
            if "width" in track_dict and "height" in track_dict:
                width = int(track_dict["width"])
                height = int(track_dict["height"])
                video_stream["width"] = width
                video_stream["height"] = height
                video_stream["resolution"] = f"{width}x{height}"

                # Calculate aspect ratio
                if height > 0:
                    aspect = width / height
                    video_stream["aspect_ratio"] = round(aspect, 2)

                    # Standard aspect ratio detection
                    if 1.30 <= aspect <= 1.37:
                        video_stream["standard_aspect_ratio"] = "4:3"
                    elif 1.75 <= aspect <= 1.80:
                        video_stream["standard_aspect_ratio"] = "16:9"
                    elif 2.35 <= aspect <= 2.40:
                        video_stream["standard_aspect_ratio"] = "2.39:1 (Anamorphic)"

            # Frame rate
            if "frame_rate" in track_dict:
                try:
                    video_stream["frame_rate"] = float(track_dict["frame_rate"])
                except (ValueError, TypeError):
                    pass

            # Color information
            if "color_space" in track_dict:
                video_stream["color_space"] = track_dict["color_space"]

            if "chroma_subsampling" in track_dict:
                video_stream["chroma_subsampling"] = track_dict["chroma_subsampling"]

            if "bit_depth" in track_dict:
                video_stream["bit_depth"] = int(track_dict["bit_depth"])

            # Duration might be track-specific
            if "duration" in track_dict:
                video_stream["duration_seconds"] = float(track_dict["duration"]) / 1000

            # Add the video stream to results
            result["video_streams"].append(video_stream)

        # Process audio tracks
        for track in media_info.audio_tracks:
            track_dict = track.to_dict()
            audio_stream = {
                "index": track_dict.get(
                    "stream_identifier", track_dict.get("track_id", 0)
                ),
                "codec": track_dict.get("codec", track_dict.get("format", "unknown")),
                "codec_profile": track_dict.get("format_profile", ""),
                "bitrate": self._parse_bitrate(track_dict.get("bit_rate", "0")),
            }

            # Channels
            if "channel_s" in track_dict:
                audio_stream["channels"] = int(track_dict["channel_s"])

            # Sampling rate
            if "sampling_rate" in track_dict:
                try:
                    audio_stream["sample_rate"] = int(track_dict["sampling_rate"])
                except (ValueError, TypeError):
                    pass

            # Language
            if "language" in track_dict:
                audio_stream["language"] = track_dict["language"]

            # Duration might be track-specific
            if "duration" in track_dict:
                audio_stream["duration_seconds"] = float(track_dict["duration"]) / 1000

            # Add the audio stream to results
            result["audio_streams"].append(audio_stream)

        # Process subtitle tracks
        for track in media_info.text_tracks:
            track_dict = track.to_dict()
            subtitle_stream = {
                "index": track_dict.get(
                    "stream_identifier", track_dict.get("track_id", 0)
                ),
                "format": track_dict.get("format", "unknown"),
            }

            # Language
            if "language" in track_dict:
                subtitle_stream["language"] = track_dict["language"]

            # Add the subtitle stream to results
            result["subtitle_streams"].append(subtitle_stream)

        # Process chapter information, if available
        for track in media_info.menu_tracks:
            track_dict = track.to_dict()

            # Extract chapters if available
            chapters = []
            for key, value in track_dict.items():
                if key.startswith("_") and key.endswith("_time"):
                    chapter_idx = key[1:-5]  # Extract chapter index
                    try:
                        # Look for corresponding chapter name
                        name_key = f"_{chapter_idx}_string"
                        if name_key in track_dict:
                            chapter_name = track_dict[name_key]
                        else:
                            chapter_name = f"Chapter {chapter_idx}"

                        # Add chapter with timestamp
                        chapters.append(
                            {
                                "index": int(chapter_idx),
                                "name": chapter_name,
                                "timestamp": value,
                            }
                        )
                    except (ValueError, TypeError):
                        pass

            # Add chapters if found
            if chapters:
                result["chapters"] = sorted(chapters, key=lambda x: x["index"])

    def _extract_with_ffmpeg(self, path: Path, result: dict[str, Any]) -> None:
        """Extract video metadata using ffmpeg.

        Args:
            path: Path to the video file
            result: Dictionary to update with extracted information
        """
        if not FFMPEG_AVAILABLE:
            raise ImportError("ffmpeg is not available or probe function is missing")

        # Get ffmpeg probe data
        ffmpeg_typed = cast(FFmpegWithProbe, ffmpeg)
        probe = ffmpeg_typed.probe(str(path))

        # Extract container format information
        if "format" in probe:
            format_info = probe["format"]

            # Format name and file size
            result["container"]["format"] = format_info.get("format_name", "unknown")
            result["container"]["format_long_name"] = format_info.get(
                "format_long_name", ""
            )

            # Duration
            if "duration" in format_info:
                duration_seconds = float(format_info["duration"])
                result["container"]["duration_seconds"] = duration_seconds
                result["container"]["duration_formatted"] = self._format_duration(
                    duration_seconds
                )

            # Bitrate
            if "bit_rate" in format_info:
                try:
                    result["container"]["bitrate"] = int(format_info["bit_rate"])
                except (ValueError, TypeError):
                    pass

            # Extract container-level tags
            if "tags" in format_info:
                for key, value in format_info["tags"].items():
                    result["tags"][key.lower()] = value

        # Process streams
        for stream in probe.get("streams", []):
            stream_type = stream.get("codec_type", "").lower()

            # Common stream properties
            stream_info = {
                "index": stream.get("index", 0),
                "codec": stream.get("codec_name", "unknown"),
                "codec_long_name": stream.get("codec_long_name", ""),
                "codec_tag": stream.get("codec_tag_string", ""),
            }

            # Extract tags for the stream
            if "tags" in stream:
                stream_info["tags"] = stream["tags"]

                # Add language if available
                if "language" in stream["tags"]:
                    stream_info["language"] = stream["tags"]["language"]

            # Process by stream type
            if stream_type == "video":
                # Add video-specific information
                if "width" in stream and "height" in stream:
                    stream_info["width"] = stream["width"]
                    stream_info["height"] = stream["height"]
                    stream_info["resolution"] = f"{stream['width']}x{stream['height']}"

                # Calculate aspect ratio
                if "display_aspect_ratio" in stream:
                    stream_info["display_aspect_ratio"] = stream["display_aspect_ratio"]
                elif "width" in stream and "height" in stream and stream["height"] > 0:
                    aspect = stream["width"] / stream["height"]
                    stream_info["aspect_ratio"] = round(aspect, 2)

                # Frame rate
                if "r_frame_rate" in stream:
                    try:
                        fps_parts = stream["r_frame_rate"].split("/")
                        if len(fps_parts) == 2 and int(fps_parts[1]) > 0:
                            stream_info["frame_rate"] = round(
                                int(fps_parts[0]) / int(fps_parts[1]), 2
                            )
                    except (ValueError, ZeroDivisionError):
                        pass

                # Color information
                if "pix_fmt" in stream:
                    stream_info["pixel_format"] = stream["pix_fmt"]

                if "color_space" in stream:
                    stream_info["color_space"] = stream["color_space"]

                # Duration might be stream-specific
                if "duration" in stream:
                    stream_info["duration_seconds"] = float(stream["duration"])

                # Add to video streams
                result["video_streams"].append(stream_info)

            elif stream_type == "audio":
                # Add audio-specific information
                if "channels" in stream:
                    stream_info["channels"] = stream["channels"]

                if "sample_rate" in stream:
                    try:
                        stream_info["sample_rate"] = int(stream["sample_rate"])
                    except (ValueError, TypeError):
                        pass

                if "channel_layout" in stream:
                    stream_info["channel_layout"] = stream["channel_layout"]

                # Bit rate for audio
                if "bit_rate" in stream:
                    try:
                        stream_info["bitrate"] = int(stream["bit_rate"])
                    except (ValueError, TypeError):
                        pass

                # Duration might be stream-specific
                if "duration" in stream:
                    stream_info["duration_seconds"] = float(stream["duration"])

                # Add to audio streams
                result["audio_streams"].append(stream_info)

            elif stream_type == "subtitle":
                # Add to subtitle streams
                result["subtitle_streams"].append(stream_info)

            else:
                # Unknown stream type
                result["other_streams"].append(stream_info)

        # Extract chapters if available
        if "chapters" in probe:
            chapters = []
            for idx, chapter in enumerate(probe["chapters"]):
                chapter_info = {
                    "index": idx,
                    "start_time": float(chapter.get("start_time", 0)),
                    "end_time": float(chapter.get("end_time", 0)),
                }

                # Extract chapter title from tags if available
                if "tags" in chapter and "title" in chapter["tags"]:
                    chapter_info["name"] = chapter["tags"]["title"]
                else:
                    chapter_info["name"] = f"Chapter {idx + 1}"

                chapters.append(chapter_info)

            result["chapters"] = chapters

    def _parse_bitrate(self, bitrate_str: str) -> int:
        """Parse bitrate string to integer value.

        Args:
            bitrate_str: Bitrate string to parse

        Returns:
            Bitrate as integer in bits per second
        """
        try:
            # Try direct conversion first
            return int(bitrate_str)
        except (ValueError, TypeError):
            # Handle case where bitrate is not a direct integer
            if isinstance(bitrate_str, str):
                # Remove any non-numeric characters
                num_str = "".join(c for c in bitrate_str if c.isdigit())
                if num_str:
                    return int(num_str)
            return 0

    def _format_duration(self, seconds: float) -> str:
        """Format duration in seconds to human-readable string.

        Args:
            seconds: Duration in seconds

        Returns:
            Formatted duration string (HH:MM:SS)
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"


# Register the extractor
MetadataExtractorRegistry.register(VideoMetadataExtractor)
