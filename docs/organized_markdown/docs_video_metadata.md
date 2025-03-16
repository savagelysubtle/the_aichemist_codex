# Video Metadata Extractor

## Overview

The Video Metadata Extractor is a specialized component in The Aichemist Codex
metadata extraction framework that processes video files and extracts
comprehensive information about their content, format, and properties. This
extractor provides detailed insights into video files, enabling better media
organization, search, and analysis.

## Features

- **Container Information**: Extracts container format, file size, and bitrate.
- **Video Track Analysis**: Extracts codec, resolution, frame rate, aspect
  ratio, and color information.
- **Audio Track Analysis**: Extracts codec, channels, sample rate, and other
  audio properties.
- **Subtitle Track Detection**: Identifies subtitle streams and their formats.
- **Chapter Information**: Extracts chapter markers and timestamps when
  available.
- **Multiple Stream Support**: Properly handles files with multiple video,
  audio, and subtitle streams.
- **Technical Metadata**: Provides detailed technical information about the
  encoding and format.
- **Tag Extraction**: Extracts embedded metadata tags such as title, artist, and
  comments.
- **Format Auto-Detection**: Supports multiple video formats with automatic
  detection.
- **Caching Support**: Integrates with the caching system for improved
  performance.
- **Fallback Mechanisms**: Uses multiple extraction methods for maximum
  compatibility.

## Usage Examples

### Basic Usage

```python
from backend.src.metadata import VideoMetadataExtractor

# Create an instance of the extractor
video_extractor = VideoMetadataExtractor()

# Extract metadata from a video file
metadata = await video_extractor.extract("/path/to/video.mp4")

# Access specific metadata
container_format = metadata.get("container", {}).get("format", "unknown")
resolution = metadata.get("video_streams", [{}])[0].get("resolution", "unknown")
duration = metadata.get("container", {}).get("duration_formatted", "unknown")

print(f"Video: {container_format}, {resolution}, {duration}")
```

### Using With Cache Manager

```python
from backend.src.utils.cache_manager import CacheManager
from backend.src.metadata import VideoMetadataExtractor

# Create a cache manager
cache_manager = CacheManager()

# Initialize the extractor with caching support
video_extractor = VideoMetadataExtractor(cache_manager=cache_manager)

# Extract metadata (results will be cached)
metadata = await video_extractor.extract("/path/to/video.mp4")
```

### Processing Multiple Video Files

```python
import asyncio
from pathlib import Path
from backend.src.metadata import VideoMetadataExtractor

async def process_video_directory(directory_path):
    video_extractor = VideoMetadataExtractor()
    results = {}

    # Process all video files in a directory
    video_extensions = [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".webm"]
    for video_file in Path(directory_path).glob("*.*"):
        if video_file.suffix.lower() in video_extensions:
            metadata = await video_extractor.extract(video_file)
            results[video_file.name] = metadata

    return results

# Process all videos in a directory
video_metadata = asyncio.run(process_video_directory("/path/to/videos/"))
```

## Extracted Metadata Structure

The extractor returns a dictionary with the following main sections:

### 1. `metadata_type`

Indicates the type of metadata ("video").

### 2. `container` Section

Contains container format information:

- `format`: Container format (MP4, MKV, AVI, etc.)
- `format_long_name`: Detailed format description
- `file_size`: Size of the file in bytes
- `filename`: Name of the file
- `bitrate`: Overall bitrate in bits per second
- `duration_seconds`: Duration in seconds
- `duration_formatted`: Formatted duration (HH:MM:SS)

### 3. `video_streams` Section

Array of video streams, each containing:

- `index`: Stream index
- `codec`: Video codec (H.264, VP9, etc.)
- `codec_long_name`: Detailed codec description
- `width`: Frame width in pixels
- `height`: Frame height in pixels
- `resolution`: Combined resolution string (e.g., "1920x1080")
- `frame_rate`: Frames per second
- `aspect_ratio`: Aspect ratio as a decimal
- `standard_aspect_ratio`: Standard aspect ratio (e.g., "16:9")
- `bit_depth`: Color bit depth
- `color_space`: Color space information
- `pixel_format`: Pixel format

### 4. `audio_streams` Section

Array of audio streams, each containing:

- `index`: Stream index
- `codec`: Audio codec (AAC, MP3, etc.)
- `codec_long_name`: Detailed codec description
- `channels`: Number of audio channels
- `channel_layout`: Channel layout (stereo, 5.1, etc.)
- `sample_rate`: Sampling rate in Hz
- `bitrate`: Audio bitrate in bits per second
- `language`: Language code if available

### 5. `subtitle_streams` Section

Array of subtitle streams, each containing:

- `index`: Stream index
- `format`: Subtitle format
- `language`: Language code if available

### 6. `chapters` Section

Array of chapter information, each containing:

- `index`: Chapter index
- `name`: Chapter name or title
- `start_time`: Start time in seconds
- `end_time`: End time in seconds

### 7. `tags` Section

Dictionary of metadata tags extracted from the file:

- `title`: Video title
- `artist`: Artist or creator
- `album`: Album or collection
- `date`: Creation or release date
- Various other tags depending on the file

### 8. `extraction_method`

Indicates which method was used to extract metadata ("mediainfo" or "ffmpeg").

## Supported Formats

The extractor supports the following video formats:

- MP4 (MPEG-4 Part 14)
- AVI (Audio Video Interleave)
- MKV (Matroska)
- MOV (QuickTime)
- WMV (Windows Media Video)
- WebM
- FLV (Flash Video)
- MPEG (Moving Picture Experts Group)
- 3GP/3G2 (3rd Generation Partnership Project)
- OGV (Ogg Video)

## Extraction Methods

The Video Metadata Extractor uses two main libraries for extraction:

1. **MediaInfo**: Provides detailed technical metadata about multimedia files.
2. **FFmpeg**: A powerful multimedia framework used as a fallback method.

The extractor first attempts to use MediaInfo, which typically provides more
detailed information. If that fails or MediaInfo is not available, it falls back
to FFmpeg's probe functionality.

## Error Handling

The extractor includes comprehensive error handling for various scenarios:

- Non-existent files
- Unsupported file formats
- Corrupted video files
- Missing dependencies

If the video cannot be processed, the result will include an `error` field with
a description of the issue.

## Performance Considerations

- The extractor uses caching to avoid repeated processing of the same unchanged
  file.
- For large files, extraction is still generally quick as it only analyzes
  metadata, not the full content.
- The fallback mechanism ensures that at least basic metadata can be extracted
  even with limited dependencies.

## Dependencies

The Video Metadata Extractor has the following optional dependencies:

- `pymediainfo`: For detailed video file analysis (primary method)
- `python-ffmpeg`: For alternative video analysis when MediaInfo is not
  available

If neither library is available, the extractor will still provide basic file
information but with limited details.

## Integration with Other Components

The Video Metadata Extractor integrates with the following system components:

- `CacheManager` for efficient caching
- `MimeTypeDetector` for file type identification
- `MetadataExtractorRegistry` for automatic registration

## Troubleshooting

Common issues and solutions:

- **Missing Dependencies**: If metadata extraction is limited, install
  pymediainfo or python-ffmpeg:

  ```bash
  pip install pymediainfo python-ffmpeg
  ```

- **MediaInfo Extraction Failures**: Some highly specialized or corrupted video
  files may not be properly analyzed by MediaInfo. In these cases, the extractor
  will automatically fall back to FFmpeg if available.

- **Missing Video Information**: Certain video files, especially those with
  non-standard encodings or containers, might have incomplete metadata. The
  extractor attempts to provide as much information as possible given the
  available data.

## Future Enhancements

Planned improvements include:

- Frame extraction capabilities for thumbnail generation
- Advanced video scene detection
- Support for additional video formats
- Enhanced HDR and color profile detection
- Video quality assessment metrics
- Integration with AI-based content analysis
- Improved handling of streaming formats
