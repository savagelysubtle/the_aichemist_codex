import logging
import os
from typing import Any

from ....core.exceptions import ExtractorError
from ..extractor import Extractor

logger = logging.getLogger(__name__)


class AudioExtractor(Extractor):
    """Extractor for audio files."""

    def __init__(self):
        super().__init__()
        self._supported_extensions = {
            ".mp3",
            ".wav",
            ".ogg",
            ".flac",
            ".aac",
            ".m4a",
            ".wma",
            ".opus",
            ".aiff",
            ".mid",
            ".midi",
        }
        self._supported_mime_types = {
            "audio/mpeg",
            "audio/wav",
            "audio/ogg",
            "audio/flac",
            "audio/aac",
            "audio/mp4",
            "audio/x-ms-wma",
            "audio/opus",
            "audio/aiff",
            "audio/midi",
        }

        # Check if required libraries are available
        self._has_mutagen = self._check_mutagen()
        if not self._has_mutagen:
            logger.warning(
                "Mutagen library not found. Audio metadata extraction will be limited."
            )

    def _check_mutagen(self) -> bool:
        """Check if Mutagen library is available.

        Returns:
            True if the library is available, False otherwise
        """
        try:
            import mutagen

            return True
        except ImportError:
            return False

    def extract_metadata(self, file_path: str) -> dict[str, Any]:
        """Extract metadata from an audio file.

        Args:
            file_path: Path to the audio file

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
                "file_type": "audio",
                "extension": ext.lower(),
                "size_bytes": stat_info.st_size,
                "last_modified": stat_info.st_mtime,
                "created": stat_info.st_ctime,
            }

            # Enhanced metadata with Mutagen if available
            if self._has_mutagen:
                try:
                    import mutagen

                    audio = mutagen.File(file_path)
                    if audio:
                        # Extract duration
                        if hasattr(audio, "info") and hasattr(audio.info, "length"):
                            metadata["duration_seconds"] = audio.info.length

                        # Extract bitrate
                        if hasattr(audio, "info") and hasattr(audio.info, "bitrate"):
                            metadata["bitrate"] = audio.info.bitrate

                        # Extract sample rate
                        if hasattr(audio, "info") and hasattr(
                            audio.info, "sample_rate"
                        ):
                            metadata["sample_rate"] = audio.info.sample_rate

                        # Extract channels
                        if hasattr(audio, "info") and hasattr(audio.info, "channels"):
                            metadata["channels"] = audio.info.channels

                        # Extract common tags
                        tags = {}
                        if hasattr(audio, "tags") and audio.tags:
                            for key, value in audio.tags.items():
                                tags[key] = value
                        elif isinstance(audio, dict):
                            for key, value in audio.items():
                                if key not in ("info", "tags") and not key.startswith(
                                    "_"
                                ):
                                    tags[key] = value

                        # Map common tags to standardized keys
                        if tags:
                            metadata["tags"] = tags

                            # Extract common metadata fields
                            for title_key in ["title", "TIT2", "©nam"]:
                                if title_key in tags:
                                    metadata["title"] = self._format_tag_value(
                                        tags[title_key]
                                    )
                                    break

                            for artist_key in ["artist", "TPE1", "©ART"]:
                                if artist_key in tags:
                                    metadata["artist"] = self._format_tag_value(
                                        tags[artist_key]
                                    )
                                    break

                            for album_key in ["album", "TALB", "©alb"]:
                                if album_key in tags:
                                    metadata["album"] = self._format_tag_value(
                                        tags[album_key]
                                    )
                                    break

                            for year_key in ["year", "date", "TDRC", "TYER", "©day"]:
                                if year_key in tags:
                                    metadata["year"] = self._format_tag_value(
                                        tags[year_key]
                                    )
                                    break

                            for genre_key in ["genre", "TCON", "©gen"]:
                                if genre_key in tags:
                                    metadata["genre"] = self._format_tag_value(
                                        tags[genre_key]
                                    )
                                    break
                except Exception as e:
                    logger.warning(f"Error extracting audio metadata: {str(e)}")

            return metadata

        except Exception as e:
            logger.error(f"Error extracting metadata from {file_path}: {str(e)}")
            raise ExtractorError(
                f"Failed to extract metadata from {file_path}: {str(e)}"
            ) from e

    def extract_content(self, file_path: str) -> str:
        """Extract textual content from an audio file.

        For audio files, this returns a description of the file.

        Args:
            file_path: Path to the audio file

        Returns:
            Textual description of the audio file

        Raises:
            ExtractorError: If content extraction fails
        """
        if not os.path.exists(file_path):
            raise ExtractorError(f"File not found: {file_path}")

        try:
            # Get metadata to create a description
            metadata = self.extract_metadata(file_path)

            description = f"[Audio: {os.path.basename(file_path)}]\n"

            # Add basic information
            if "title" in metadata:
                description += f"Title: {metadata['title']}\n"
            if "artist" in metadata:
                description += f"Artist: {metadata['artist']}\n"
            if "album" in metadata:
                description += f"Album: {metadata['album']}\n"
            if "year" in metadata:
                description += f"Year: {metadata['year']}\n"
            if "genre" in metadata:
                description += f"Genre: {metadata['genre']}\n"

            # Add technical information
            if "duration_seconds" in metadata:
                minutes, seconds = divmod(int(metadata["duration_seconds"]), 60)
                description += f"Duration: {minutes}:{seconds:02d}\n"
            if "bitrate" in metadata:
                description += f"Bitrate: {int(metadata['bitrate'] / 1000)} kbps\n"
            if "sample_rate" in metadata:
                description += f"Sample Rate: {metadata['sample_rate']} Hz\n"
            if "channels" in metadata:
                description += f"Channels: {metadata['channels']}\n"

            # Attempt transcription if available
            try:
                import speech_recognition as sr

                # Check if file is a supported format for speech recognition
                if metadata["extension"].lower() in [".wav"]:
                    recognizer = sr.Recognizer()
                    with sr.AudioFile(file_path) as source:
                        audio_data = recognizer.record(source)
                        try:
                            text = recognizer.recognize_google(audio_data)
                            description += f"\nTranscription:\n{text}\n"
                        except sr.UnknownValueError:
                            description += "\nSpeech could not be transcribed\n"
            except ImportError:
                # Speech recognition library not available
                pass
            except Exception as e:
                logger.warning(f"Transcription failed: {str(e)}")

            return description

        except Exception as e:
            logger.error(f"Error extracting content from {file_path}: {str(e)}")
            raise ExtractorError(
                f"Failed to extract content from {file_path}: {str(e)}"
            ) from e

    def generate_preview(self, file_path: str, max_size: int = 1000) -> str:
        """Generate a textual preview of the audio file.

        Args:
            file_path: Path to the audio file
            max_size: Maximum size of the preview in characters

        Returns:
            A textual description of the audio file

        Raises:
            ExtractorError: If preview generation fails
        """
        try:
            # For audio files, we just return a description
            description = self.extract_content(file_path)

            if len(description) <= max_size:
                return description
            else:
                return description[:max_size] + "..."

        except Exception as e:
            logger.error(f"Error generating preview for {file_path}: {str(e)}")
            raise ExtractorError(
                f"Failed to generate preview for {file_path}: {str(e)}"
            ) from e

    def _format_tag_value(self, value: Any) -> str:
        """Format a tag value as a string.

        Args:
            value: The tag value

        Returns:
            Formatted string value
        """
        if isinstance(value, (list, tuple)):
            # Join list values with commas
            return ", ".join(str(v) for v in value)
        elif isinstance(value, bytes):
            # Try to decode bytes to string
            try:
                return value.decode("utf-8")
            except UnicodeDecodeError:
                return str(value)
        else:
            # Convert other types to string
            return str(value)
