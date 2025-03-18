import os
import logging
from typing import Dict, Any, Set, Optional

from ..extractor import Extractor
from ....core.exceptions import ExtractorError

logger = logging.getLogger(__name__)

class VideoExtractor(Extractor):
    """Extractor for video files."""

    def __init__(self):
        super().__init__()
        self._supported_extensions = {
            ".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv",
            ".webm", ".m4v", ".mpg", ".mpeg", ".3gp", ".ts"
        }
        self._supported_mime_types = {
            "video/mp4", "video/x-msvideo", "video/x-matroska",
            "video/quicktime", "video/x-ms-wmv", "video/x-flv",
            "video/webm", "video/mpeg", "video/3gpp"
        }

        # Check if required libraries are available
        self._has_ffmpeg = self._check_ffmpeg()
        if not self._has_ffmpeg:
            logger.warning("ffmpeg-python library not found. Video metadata extraction will be limited.")

    def _check_ffmpeg(self) -> bool:
        """Check if ffmpeg-python library is available.

        Returns:
            True if the library is available, False otherwise
        """
        try:
            import ffmpeg
            return True
        except ImportError:
            return False

    def extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract metadata from a video file.

        Args:
            file_path: Path to the video file

        Returns:
            Dictionary containing metadata

        Raises:
            ExtractorError: If metadata extraction fails
        """
        if not os.path.exists(file_path):
            raise ExtractorError(f"File not found: {file_path}")

        try:
            # Basic file info
            stat_info = os.stat(file_path)
            _, ext = os.path.splitext(file_path)

            metadata = {
                "file_type": "video",
                "extension": ext.lower(),
                "size_bytes": stat_info.st_size,
                "last_modified": stat_info.st_mtime,
                "created": stat_info.st_ctime,
            }

            # Enhanced metadata with ffmpeg if available
            if self._has_ffmpeg:
                try:
                    import ffmpeg

                    probe_data = ffmpeg.probe(file_path)

                    # Get video stream info
                    video_streams = [stream for stream in probe_data.get("streams", [])
                                    if stream.get("codec_type") == "video"]
                    if video_streams:
                        video_stream = video_streams[0]
                        metadata["width"] = int(video_stream.get("width", 0))
                        metadata["height"] = int(video_stream.get("height", 0))
                        metadata["codec"] = video_stream.get("codec_name", "unknown")
                        if "avg_frame_rate" in video_stream:
                            frame_rate = video_stream["avg_frame_rate"]
                            if "/" in frame_rate:
                                num, den = map(int, frame_rate.split("/"))
                                if den != 0:  # Avoid division by zero
                                    metadata["frame_rate"] = round(num / den, 2)

                    # Get audio stream info
                    audio_streams = [stream for stream in probe_data.get("streams", [])
                                    if stream.get("codec_type") == "audio"]
                    if audio_streams:
                        audio_stream = audio_streams[0]
                        metadata["audio_codec"] = audio_stream.get("codec_name", "unknown")
                        metadata["audio_channels"] = int(audio_stream.get("channels", 0))
                        metadata["audio_sample_rate"] = int(audio_stream.get("sample_rate", 0))

                    # Get format info (includes duration)
                    format_info = probe_data.get("format", {})
                    if "duration" in format_info:
                        metadata["duration_seconds"] = float(format_info["duration"])
                    if "bit_rate" in format_info:
                        metadata["bitrate"] = int(format_info["bit_rate"])

                    # Get metadata from format tags
                    tags = format_info.get("tags", {})
                    if tags:
                        metadata["tags"] = {}
                        for key, value in tags.items():
                            metadata["tags"][key.lower()] = value

                        # Extract common metadata fields
                        if "title" in tags:
                            metadata["title"] = tags["title"]
                        if "artist" in tags:
                            metadata["artist"] = tags["artist"]
                        if "date" in tags:
                            metadata["date"] = tags["date"]
                        if "genre" in tags:
                            metadata["genre"] = tags["genre"]
                except Exception as e:
                    logger.warning(f"Error extracting video metadata with ffmpeg: {str(e)}")

            return metadata

        except Exception as e:
            logger.error(f"Error extracting metadata from {file_path}: {str(e)}")
            raise ExtractorError(f"Failed to extract metadata from {file_path}: {str(e)}") from e

    def extract_content(self, file_path: str) -> str:
        """Extract textual content from a video file.

        For video files, this returns a description of the file.

        Args:
            file_path: Path to the video file

        Returns:
            Textual description of the video file

        Raises:
            ExtractorError: If content extraction fails
        """
        if not os.path.exists(file_path):
            raise ExtractorError(f"File not found: {file_path}")

        try:
            # Get metadata to create a description
            metadata = self.extract_metadata(file_path)

            description = f"[Video: {os.path.basename(file_path)}]\n"

            # Add basic information
            if "title" in metadata:
                description += f"Title: {metadata['title']}\n"
            if "artist" in metadata:
                description += f"Creator: {metadata['artist']}\n"
            if "date" in metadata:
                description += f"Date: {metadata['date']}\n"
            if "genre" in metadata:
                description += f"Genre: {metadata['genre']}\n"

            return description