# Audio Metadata Extraction

## Overview

The audio metadata extraction module provides comprehensive capabilities for
extracting rich metadata from various audio formats. This module is part of The
Aichemist Codex's Expanded Format Support, enabling intelligent analysis and
organization of audio files.

The extractor can process multiple audio formats (MP3, WAV, FLAC, OGG, AAC,
etc.) and extracts a wide range of metadata including technical audio
properties, ID3 tags, and format-specific details. This enables powerful
searching, organization, and analysis of audio content.

## Features

- **Format Detection**: Automatically identify and process various audio formats
- **Technical Properties**: Extract duration, bitrate, sample rate, channels,
  and encoding
- **ID3 Tags**: Extract artist, album, title, genre, year, and other standard
  tags
- **Album Art Detection**: Identify the presence of embedded album artwork
- **Audio Analysis**: Basic audio characteristics analysis including dBFS
  (decibels relative to full scale)
- **Comprehensive Tag Support**: Support for MP3 ID3, FLAC, Ogg Vorbis, and
  MP4/AAC tags
- **Section Analysis**: Extract audio characteristics from beginning, middle,
  and end of files

## Usage

### Basic Usage

```python
from backend.src.metadata import AudioMetadataExtractor

# Create an instance of the extractor
extractor = AudioMetadataExtractor()

# Extract metadata from an audio file
metadata = await extractor.extract("/path/to/audio.mp3")

# Use the extracted metadata
if "artist" in metadata["tags"]:
    artist = metadata["tags"]["artist"]
    title = metadata["tags"].get("title", "Unknown Track")
    print(f"Playing: {title} by {artist}")
```

### With Cache Manager

For performance optimization, you can provide a cache manager:

```python
from backend.src.metadata import AudioMetadataExtractor
from backend.src.utils.cache_manager import CacheManager

# Create a cache manager
cache_manager = CacheManager()

# Create an instance of the extractor with cache support
extractor = AudioMetadataExtractor(cache_manager=cache_manager)

# Extract metadata (this will use/update the cache)
metadata = await extractor.extract("/path/to/audio.mp3")
```

## Extracted Metadata

The extractor returns a dictionary with the following structure:

```python
{
    "metadata_type": "audio",
    "format": {
        "encoding": "mp3",         # Audio encoding format
        "duration": 235.42,        # Duration in seconds
        "bitrate": 320000,         # Bitrate in bits per second
        "sample_rate": 44100,      # Sample rate in Hz
        "channels": 2,             # Number of audio channels
        "stereo_mode": 0,          # MP3 stereo mode (0: Stereo, 1: Joint Stereo, etc.)
        "sample_width_bytes": 2,   # Sample width in bytes
        "frame_rate": 44100,       # Frame rate (samples per second)
        "frame_width": 4,          # Frame width in bytes
        "duration_ms": 235420      # Duration in milliseconds
    },
    "tags": {
        "artist": "The Beatles",
        "title": "Here Comes the Sun",
        "album": "Abbey Road",
        "genre": "Rock",
        "date": "1969",
        "tracknumber": "7",
        # Other format-specific tags will appear here
    },
    "analysis": {
        "max_dBFS": -0.5,          # Maximum dBFS (decibels relative to full scale)
        "dBFS": -15.7,             # Average dBFS
        "rms": 0.085,              # Root mean square amplitude
        "sections": {              # Analysis of different sections
            "start": {
                "dBFS": -18.2,
                "rms": 0.038
            },
            "middle": {
                "dBFS": -14.3,
                "rms": 0.096
            },
            "end": {
                "dBFS": -17.1,
                "rms": 0.044
            }
        }
    },
    "has_album_art": True          # Presence of embedded album artwork
}
```

> **Note**: Not all fields will be present for all audio files. The content
> depends on what metadata is available in the original file and the specific
> format.

## Supported Audio Formats

The extractor supports the following audio formats:

- MP3
- WAV/WAVE
- FLAC
- OGG Vorbis
- AAC
- M4A/MP4 Audio
- WebM Audio

## Error Handling

The extractor implements robust error handling to ensure it doesn't fail when
processing problematic audio files:

- Missing files are reported as warnings
- Unsupported file types are gracefully skipped
- Corrupted tag data is handled safely
- Format-specific errors are caught and logged
- Errors are logged with appropriate severity levels

## Performance Considerations

- **Caching**: Use the cache manager for repeated access to the same files
- **Selective Processing**: The extractor uses a two-stage approach with Mutagen
  for metadata and PyDub for audio characteristics
- **Format-Specific Optimization**: Different audio formats are processed with
  specialized handlers
- **Efficient Section Analysis**: Analysis of audio characteristics focuses on
  representative sections rather than processing entire files

## Implementation Details

### Audio Tag Processing

Audio tag data is extracted using the Mutagen library, which offers
comprehensive support for various audio formats. The extractor includes
specialized processing for different formats:

- **MP3**: ID3 tags are processed with special handling for different frame
  types
- **FLAC**: Built-in tag handling with support for embedded pictures
- **OGG**: Vorbis comment extraction and normalization
- **MP4/AAC**: iTunes-style tag processing with mapping to standardized names

### Audio Characteristics Analysis

Technical audio characteristics are extracted using both Mutagen (for format
info) and PyDub (for audio analysis):

- **Format Information**: Encoding, bitrate, sample rate, duration
- **Channel Configuration**: Stereo/mono detection and channel count
- **Audio Properties**: dBFS levels, RMS values, and section analysis
- **Safe Property Extraction**: Properties are accessed safely with appropriate
  error handling

### Safety Features

The extractor includes several safety mechanisms:

- Type checking and validation
- Defensive attribute access
- Exception handling with appropriate logging
- Cache key generation based on modification time
- Format-specific error handling

## Integration with Other Components

The audio metadata extractor integrates with several other components in The
Aichemist Codex:

- **File Manager**: Provides supplementary information for audio file operations
- **Search**: Enables searching by audio properties and tags
- **Auto-Tagging**: Supplies metadata for automatic categorization of audio
  files
- **Relationships**: Can establish connections between related audio files
- **File Similarity**: Contributes data points for audio similarity algorithms

## Configuration

The audio metadata extractor has no specific configuration options beyond the
cache manager. It automatically adapts to the available information in each
audio file.

## Next Steps and Future Enhancements

Planned improvements for the audio metadata extraction include:

- Enhanced spectral analysis capabilities
- Voice detection and speaker identification
- Music genre classification using machine learning
- BPM (beats per minute) detection
- Audio fingerprinting for duplicate detection
- Lyrics extraction and processing
- More comprehensive audio quality assessment
- Integration with music databases for extended metadata
- Support for additional audio formats and tag standards
