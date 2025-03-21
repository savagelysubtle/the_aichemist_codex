"""
Audio metadata extraction for The Aichemist Codex.

This module provides functionality to extract metadata from audio files,
including format information, duration, bitrate, sample rate, and other
audio-specific metadata like ID3 tags.
"""

import logging
from pathlib import Path
from typing import Any, TypeVar

# Import File directly from mutagen
import mutagen
from mutagen.flac import FLAC
from mutagen.id3 import ID3
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4
from mutagen.oggvorbis import OggVorbis

from the_aichemist_codex.backend.file_reader.file_metadata import FileMetadata
from the_aichemist_codex.backend.metadata.extractor import (
    BaseMetadataExtractor,
    MetadataExtractorRegistry,
)
from the_aichemist_codex.backend.utils.cache.cache_manager import CacheManager
from the_aichemist_codex.backend.utils.io.mime_type_detector import MimeTypeDetector

# Type aliases for better type checking
AudioFile = TypeVar("AudioFile")
AudioInfo = TypeVar("AudioInfo")

# Handle optional dependencies
AUDIO_LIBS_AVAILABLE = False
AudioSegment = None  # Initialize as None
try:
    # Attempt to import pydub
    import pydub
    from pydub import AudioSegment

    AUDIO_LIBS_AVAILABLE = True
except ImportError:
    # Dependency not available, will handle gracefully at runtime
    logger = logging.getLogger(__name__)
    logger.warning(
        "pydub or audioop/pyaudioop dependency is missing. Some audio features will be disabled."
    )


logger = logging.getLogger(__name__)


class AudioMetadataExtractor(BaseMetadataExtractor):
    """
    Metadata extractor for audio files.

    This extractor can process various audio formats (MP3, WAV, FLAC, OGG, etc.)
    and extract rich metadata including:
    - File format and encoding
    - Duration, bitrate, sample rate, and channels
    - ID3 tags (artist, album, title, genre, etc.)
    - Album art (if available)
    - Technical audio characteristics
    """

    # Supported MIME types
    SUPPORTED_MIME_TYPES = [
        "audio/mpeg",
        "audio/mp3",
        "audio/wav",
        "audio/wave",
        "audio/x-wav",
        "audio/flac",
        "audio/ogg",
        "audio/aac",
        "audio/mp4",
        "audio/x-m4a",
        "audio/webm",
    ]

    # Mapping from file extensions to pydub formats
    PYDUB_FORMAT_MAP = {
        ".mp3": "mp3",
        ".wav": "wav",
        ".wave": "wav",
        ".flac": "flac",
        ".ogg": "ogg",
        ".aac": "aac",
        ".m4a": "mp4",
        ".webm": "webm",
    }

    def __init__(self, cache_manager: CacheManager | None = None):
        """Initialize the audio metadata extractor.

        Args:
            cache_manager: Optional cache manager for caching extraction results
        """
        super().__init__(cache_manager)
        self.mime_detector = MimeTypeDetector()
        if not AUDIO_LIBS_AVAILABLE:
            logger.warning(
                "Audio libraries not available: pydub or audioop/pyaudioop missing"
            )

    @property
    def supported_mime_types(self) -> list[str]:
        """List of MIME types supported by this extractor.

        Returns:
            list[str]: A list of MIME type strings that this extractor can handle
        """
        return self.SUPPORTED_MIME_TYPES

    async def extract(
        self,
        file_path: str | Path,
        content: str | None = None,
        mime_type: str | None = None,
        metadata: FileMetadata | None = None,
    ) -> dict[str, Any]:
        """
        Extract metadata from an audio file.

        Args:
            file_path: Path to the audio file
            content: Not used for audio files
            mime_type: Optional MIME type of the file
            metadata: Optional existing metadata to enhance

        Returns:
            Dictionary containing extracted audio metadata
        """
        path = Path(file_path)
        if not path.exists():
            logger.warning(f"Audio file not found: {path}")
            return {}

        if not AUDIO_LIBS_AVAILABLE:
            return {
                "error": "Audio libraries not available",
                "file_path": str(path),
                "type": "audio",
                "format": path.suffix.lstrip(".").lower(),
                "duration_seconds": 0,
                "channels": 0,
                "sample_rate": 0,
                "bit_rate": 0,
            }

        # Determine MIME type if not provided
        if mime_type is None:
            mime_type, _ = self.mime_detector.get_mime_type(path)

        # Check if this is a supported audio type
        if mime_type not in self.SUPPORTED_MIME_TYPES:
            logger.debug(f"Unsupported audio type: {mime_type} for file: {path}")
            return {}

        # Try to use cache if available
        if self.cache_manager:
            cache_key = f"audio_metadata:{path}:{path.stat().st_mtime}"
            cached_data = await self.cache_manager.get(cache_key)
            if cached_data:
                logger.debug(f"Using cached audio metadata for {path}")
                return cached_data

        # Process the audio file
        try:
            result = await self._process_audio(path)

            # Cache the result if cache manager is available
            if self.cache_manager:
                await self.cache_manager.put(cache_key, result)

            return result
        except Exception as e:
            logger.error(f"Error extracting audio metadata from {path}: {str(e)}")
            return {}

    async def _process_audio(self, path: Path) -> dict[str, Any]:
        """
        Process an audio file to extract metadata.

        Args:
            path: Path to the audio file

        Returns:
            Dictionary containing extracted audio metadata
        """
        result = {
            "metadata_type": "audio",
            "format": {},
            "tags": {},
        }

        # Extract format-specific data using Mutagen
        try:
            mutagen_data = self._extract_mutagen_metadata(path)
            if mutagen_data:
                result.update(mutagen_data)
        except Exception as e:
            logger.debug(f"Error extracting Mutagen metadata: {str(e)}")

        # Extract audio characteristics using PyDub
        try:
            pydub_data = self._extract_pydub_metadata(path)
            if pydub_data:
                # Merge with existing format data
                result["format"].update(pydub_data.get("format", {}))

                # Add analysis data
                if "analysis" in pydub_data:
                    result["analysis"] = pydub_data["analysis"]
        except Exception as e:
            logger.debug(f"Error extracting PyDub metadata: {str(e)}")

        return result

    def _extract_mutagen_metadata(self, path: Path) -> dict[str, Any]:
        """
        Extract audio metadata using Mutagen.

        Args:
            path: Path to the audio file

        Returns:
            Dictionary containing metadata extracted with Mutagen
        """
        result = {"format": {}, "tags": {}}
        file_ext = path.suffix.lower()

        try:
            # Process different audio formats
            if file_ext == ".mp3":
                self._process_mp3(path, result)
            elif file_ext == ".flac":
                self._process_flac(path, result)
            elif file_ext == ".ogg":
                self._process_ogg(path, result)
            elif file_ext in [".m4a", ".mp4", ".aac"]:
                self._process_mp4(path, result)
            else:
                # Generic handling for other formats
                audio_file = mutagen.File(str(path))  # type: ignore
                if audio_file:
                    self._extract_generic_tags(audio_file, result)
                    if hasattr(audio_file, "info"):
                        info = audio_file.info
                        # Safely extract common properties
                        self._safe_extract_audio_info(info, result)
        except Exception as e:
            logger.debug(f"Mutagen processing error for {path}: {str(e)}")

        return result

    def _safe_extract_audio_info(self, info: Any, result: dict[str, Any]) -> None:
        """
        Safely extract common audio information properties.

        Args:
            info: Audio info object from Mutagen
            result: Dictionary to update with extracted information
        """
        # Extract duration which is common in all formats
        if hasattr(info, "length"):
            result["format"]["duration"] = info.length

        # Safely extract other common properties
        for attr in ["bitrate", "sample_rate", "channels", "layer", "bits_per_sample"]:
            if hasattr(info, attr):
                value = getattr(info, attr)
                if value is not None:
                    result["format"][attr] = value

        # Special handling for MP3 mode attribute since it's causing linter issues
        if hasattr(info, "mode") and info.__class__.__name__ == "MPEGInfo":
            # For MP3 files, mode indicates stereo mode
            # 0: Stereo, 1: Joint Stereo, 2: Dual Channel, 3: Mono
            mode_value = info.mode
            result["format"]["channels"] = 1 if mode_value == 3 else 2
            result["format"]["stereo_mode"] = mode_value

    def _process_mp3(self, path: Path, result: dict[str, Any]) -> None:
        """
        Process MP3 file and extract metadata.

        Args:
            path: Path to the MP3 file
            result: Dictionary to update with extracted metadata
        """
        try:
            mp3 = MP3(path)

            # Format information
            result["format"]["encoding"] = "mp3"
            # Use safe extraction with common attributes
            self._safe_extract_audio_info(mp3.info, result)

            # Try to get ID3 tags
            try:
                id3 = ID3(path)
                for key in id3:
                    frame = id3[key]
                    text = None

                    # Extract text from different tag types
                    if hasattr(frame, "text"):
                        text = frame.text
                    elif hasattr(frame, "data"):
                        text = frame.data

                    # Process text data
                    if text:
                        if isinstance(text, list) and len(text) == 1:
                            result["tags"][key] = str(text[0])
                        else:
                            result["tags"][key] = str(text)

                # Common ID3 tags mapping
                tag_mapping = {
                    "TPE1": "artist",
                    "TIT2": "title",
                    "TALB": "album",
                    "TCON": "genre",
                    "TDRC": "date",
                    "TRCK": "tracknumber",
                }

                # Map to common names
                for id3_tag, common_name in tag_mapping.items():
                    if id3_tag in result["tags"]:
                        result["tags"][common_name] = result["tags"][id3_tag]
            except Exception as e:
                logger.debug(f"Error extracting ID3 tags: {str(e)}")

            # Check for album art
            if hasattr(mp3, "tags") and mp3.tags:
                for key in mp3.tags.keys():
                    if key.startswith("APIC:"):
                        result["has_album_art"] = True
                        break
        except Exception as e:
            logger.debug(f"Error processing MP3 file {path}: {str(e)}")

    def _process_flac(self, path: Path, result: dict[str, Any]) -> None:
        """
        Process FLAC file and extract metadata.

        Args:
            path: Path to the FLAC file
            result: Dictionary to update with extracted metadata
        """
        try:
            flac = FLAC(path)

            # Format information
            result["format"]["encoding"] = "flac"
            # Use safe extraction for common attributes
            self._safe_extract_audio_info(flac.info, result)

            # Tags
            for key, value in flac.items():
                if isinstance(value, list) and len(value) == 1:
                    result["tags"][key.lower()] = value[0]
                else:
                    result["tags"][key.lower()] = value

            # Check for pictures/album art
            if hasattr(flac, "pictures") and flac.pictures:
                result["has_album_art"] = True
        except Exception as e:
            logger.debug(f"Error processing FLAC file {path}: {str(e)}")

    def _process_ogg(self, path: Path, result: dict[str, Any]) -> None:
        """
        Process OGG file and extract metadata.

        Args:
            path: Path to the OGG file
            result: Dictionary to update with extracted metadata
        """
        try:
            ogg = OggVorbis(path)

            # Format information
            result["format"]["encoding"] = "vorbis"
            # Use safe extraction for common attributes
            self._safe_extract_audio_info(ogg.info, result)

            # Tags
            for key, value in ogg.items():
                if isinstance(value, list) and len(value) == 1:
                    result["tags"][key.lower()] = value[0]
                else:
                    result["tags"][key.lower()] = value
        except Exception as e:
            logger.debug(f"Error processing OGG file {path}: {str(e)}")

    def _process_mp4(self, path: Path, result: dict[str, Any]) -> None:
        """
        Process MP4/M4A/AAC file and extract metadata.

        Args:
            path: Path to the MP4 file
            result: Dictionary to update with extracted metadata
        """
        try:
            mp4 = MP4(path)

            # Format information
            result["format"]["encoding"] = (
                "aac" if path.suffix.lower() == ".aac" else "mp4"
            )
            # Use safe extraction for common attributes
            self._safe_extract_audio_info(mp4.info, result)

            # Map common MP4 tags to standard names
            tag_mapping = {
                "©nam": "title",
                "©ART": "artist",
                "©alb": "album",
                "©gen": "genre",
                "©day": "date",
                "©wrt": "composer",
                "trkn": "tracknumber",
                "disk": "discnumber",
                "©cmt": "comment",
            }

            # Process tags
            for key, value in mp4.items():
                if key in tag_mapping:
                    tag_name = tag_mapping[key]
                    if isinstance(value, list) and len(value) == 1:
                        result["tags"][tag_name] = value[0]
                    else:
                        result["tags"][tag_name] = value

            # Check for album art
            if "covr" in mp4:
                result["has_album_art"] = True
        except Exception as e:
            logger.debug(f"Error processing MP4 file {path}: {str(e)}")

    def _extract_generic_tags(self, audio_file: Any, result: dict[str, Any]) -> None:
        """
        Extract tags from a generic audio file.

        Args:
            audio_file: Mutagen audio file object
            result: Dictionary to update with extracted tags
        """
        if hasattr(audio_file, "tags") and audio_file.tags:
            for key, value in audio_file.tags.items():
                if hasattr(value, "text"):
                    # Handle ID3 style tags
                    if isinstance(value.text, list) and len(value.text) == 1:
                        result["tags"][key.lower()] = value.text[0]
                    else:
                        result["tags"][key.lower()] = value.text
                else:
                    # Handle simple tag values
                    if isinstance(value, list) and len(value) == 1:
                        result["tags"][key.lower()] = value[0]
                    else:
                        result["tags"][key.lower()] = value

    def _extract_pydub_metadata(self, path: Path) -> dict[str, Any]:
        """
        Extract audio metadata using PyDub.

        Args:
            path: Path to the audio file

        Returns:
            Dictionary containing metadata extracted with PyDub
        """
        if not AUDIO_LIBS_AVAILABLE or AudioSegment is None:
            return {"format": {}}  # Return empty dict when PyDub is not available

        result = {"format": {}}
        file_ext = path.suffix.lower()

        try:
            # Determine PyDub format
            pydub_format = self.PYDUB_FORMAT_MAP.get(file_ext)
            if not pydub_format:
                logger.debug(f"Unsupported PyDub format for extension: {file_ext}")
                return result

            # Load audio with PyDub
            audio = AudioSegment.from_file(str(path), format=pydub_format)

            # Extract basic format info
            result["format"].update(
                {
                    "duration_seconds": len(audio) / 1000,
                    "channels": audio.channels,
                    "sample_rate": audio.frame_rate,
                    "bit_depth": audio.sample_width * 8,
                    "bit_rate": audio.frame_rate * audio.frame_width * 8,
                }
            )

            # Add audio section analysis if the file isn't too large
            if len(audio) < 300000:  # Limit to 5 minutes of audio for performance
                # Instead of calling _analyze_audio, do the analysis directly here
                analysis = {}

                # Calculate dBFS (decibels relative to full scale)
                analysis["max_dBFS"] = audio.max_dBFS
                analysis["dBFS"] = audio.dBFS

                # Add RMS (root mean square)
                analysis["rms"] = audio.rms

                result["analysis"] = analysis

        except Exception as e:
            logger.debug(f"PyDub processing error for {path}: {str(e)}")

        return result

    def supports_file(self, file_path: str | Path) -> bool:
        """
        Check if this extractor supports the given file.

        Args:
            file_path: Path to the file to check

        Returns:
            True if this extractor supports the file, False otherwise
        """
        # Skip if audio libraries are not available
        if not AUDIO_LIBS_AVAILABLE or AudioSegment is None:
            return False

        path = Path(file_path)
        if not path.exists():
            return False

        # Check if the file is a supported audio type
        mime_type, _ = self.mime_detector.get_mime_type(path)
        if mime_type in self.SUPPORTED_MIME_TYPES:
            return True

        # Check file extension
        return path.suffix.lower() in self.PYDUB_FORMAT_MAP


# Register the extractor
MetadataExtractorRegistry.register(AudioMetadataExtractor)
