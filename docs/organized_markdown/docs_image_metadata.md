# Image Metadata Extraction

## Overview

The image metadata extraction module provides advanced capabilities for
extracting rich metadata from various image formats. This module is part of The
Aichemist Codex's Expanded Format Support and enables intelligent analysis of
image files.

The extractor can process multiple image formats (JPEG, PNG, TIFF, GIF, etc.)
and extracts a wide range of metadata including EXIF information, image
dimensions, color profiles, and other format-specific details.

## Features

- **EXIF Data Extraction**: Comprehensive extraction of EXIF metadata including
  camera settings, capture date/time, and GPS coordinates
- **Image Properties**: Extract dimensions, resolution, color modes, and aspect
  ratio
- **Camera Information**: Access make, model, lens, and exposure settings
- **Geolocation**: Convert GPS coordinates to usable decimal degrees format
- **Animation Detection**: Identify and extract information about animated GIFs
- **Transparency Information**: Detect transparency in supported formats
- **Color Profiles**: Identify ICC profile presence
- **Thumbnail Detection**: Detect embedded thumbnails in images

## Usage

### Basic Usage

```python
from backend.src.metadata import ImageMetadataExtractor

# Create an instance of the extractor
extractor = ImageMetadataExtractor()

# Extract metadata from an image file
metadata = await extractor.extract("/path/to/image.jpg")

# Use the extracted metadata
if "gps" in metadata["exif"]:
    latitude = metadata["exif"]["gps"]["latitude"]
    longitude = metadata["exif"]["gps"]["longitude"]
    print(f"Image was taken at coordinates: {latitude}, {longitude}")
```

### With Cache Manager

For performance optimization, you can provide a cache manager:

```python
from backend.src.metadata import ImageMetadataExtractor
from backend.src.utils.cache_manager import CacheManager

# Create a cache manager
cache_manager = CacheManager()

# Create an instance of the extractor with cache support
extractor = ImageMetadataExtractor(cache_manager=cache_manager)

# Extract metadata (this will use/update the cache)
metadata = await extractor.extract("/path/to/image.jpg")
```

## Extracted Metadata

The extractor returns a dictionary with the following structure:

```python
{
    "metadata_type": "image",
    "format": "JPEG",  # Image format (JPEG, PNG, GIF, etc.)
    "mode": "RGB",     # Color mode
    "dimensions": {
        "width": 3840,
        "height": 2160,
        "aspect_ratio": 1.778  # Width/height ratio
    },
    "resolution": {
        "dpi_x": 300,
        "dpi_y": 300
    },
    "has_color_profile": True,  # Presence of ICC profile
    "has_transparency": False,  # Transparency information
    "exif": {
        "camera": {
            "make": "Canon",
            "model": "EOS 5D Mark IV"
        },
        "lens": {
            "make": "Canon",
            "model": "EF 24-70mm f/2.8L II USM",
            "focal_length": 50.0
        },
        "exposure": {
            "exposure_time": 0.005,  # 1/200 second
            "f_number": 4.0,
            "iso": 100,
            "program": 1
        },
        "capture_datetime": "2023:06:15 14:30:22",
        "gps": {
            "latitude": 40.7128,
            "longitude": -74.0060,
            "altitude": 10.5
        },
        # ... other EXIF data
    },
    "animation": {  # Only for animated images
        "frame_count": 24,
        "duration": 100  # milliseconds per frame
    },
    "has_thumbnail": True  # JPEG embedded thumbnail presence
}
```

> **Note**: Not all fields will be present for all images. The content depends
> on what metadata is available in the original file.

## Supported Image Formats

The extractor supports the following image formats:

- JPEG/JPG
- PNG
- TIFF
- GIF (including animated GIFs)
- BMP
- WebP

## Error Handling

The extractor implements robust error handling to ensure it doesn't fail when
processing problematic images:

- Missing files are reported as warnings
- Unsupported file types are gracefully skipped
- Corrupted EXIF data is handled safely
- Binary data is summarized rather than included verbatim
- Errors are logged with appropriate severity levels

## Performance Considerations

- **Caching**: Use the cache manager for repeated access to the same files
- **Selective Extraction**: If you only need specific metadata, consider
  creating a custom extension that extracts only what you need
- **Large Files**: For very large image collections, consider implementing batch
  processing

## Implementation Details

### EXIF Processing

EXIF data is extracted from images using Pillow's internal APIs. The data is
then processed to normalize formats and extract the most valuable information.
Special handling is provided for:

- GPS coordinates (converted to decimal degrees)
- Timestamps (formatted consistently)
- Camera and lens information (organized into logical groups)
- Exposure settings (normalized into standard units)

### Animation Detection

For GIF files, the extractor checks for animation properties including frame
count and duration. This information can be useful for media management
applications.

### Safety Features

The extractor includes several safety mechanisms:

- Type checking and validation
- Defensive attribute access
- Exception handling with appropriate logging
- Cache key generation based on modification time

## Integration with Other Components

The image metadata extractor integrates with several other components in The
Aichemist Codex:

- **File Manager**: Provides supplementary information for file operations
- **Search**: Enables searching by image properties
- **Auto-Tagging**: Supplies metadata for automatic categorization
- **Relationships**: Can establish connections between similar images
- **File Similarity**: Contributes data points for similarity algorithms

## Configuration

The image metadata extractor has no specific configuration options beyond the
cache manager. It automatically adapts to the available information in each
image file.

## Next Steps and Future Enhancements

Planned improvements for the image metadata extraction include:

- Enhanced face detection capabilities
- Object recognition using ML models
- Color palette extraction
- Duplicate image detection based on visual fingerprinting
- Watermark detection
- Image quality assessment
