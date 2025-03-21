"""
Image metadata extraction for The Aichemist Codex.

This module provides functionality to extract metadata from image files,
including EXIF data, image dimensions, color profiles, and other image-specific
information.
"""

import logging
from pathlib import Path
from typing import Any

from PIL import Image
from PIL.ExifTags import GPSTAGS, TAGS

from the_aichemist_codex.backend.file_reader.file_metadata import FileMetadata
from the_aichemist_codex.backend.metadata.extractor import (
    BaseMetadataExtractor,
    MetadataExtractorRegistry,
)
from the_aichemist_codex.backend.utils.cache.cache_manager import CacheManager
from the_aichemist_codex.backend.utils.io.mime_type_detector import MimeTypeDetector

logger = logging.getLogger(__name__)


class ImageMetadataExtractor(BaseMetadataExtractor):
    """
    Metadata extractor for image files.

    This extractor can process various image formats (JPEG, PNG, TIFF, etc.)
    and extract rich metadata including:
    - EXIF data (camera settings, date/time, GPS, etc.)
    - Image dimensions and resolution
    - Color mode and bit depth
    - Format-specific information
    """

    # Supported MIME types
    SUPPORTED_MIME_TYPES = [
        "image/jpeg",
        "image/jpg",
        "image/png",
        "image/tiff",
        "image/gif",
        "image/bmp",
        "image/webp",
    ]

    def __init__(self, cache_manager: CacheManager | None = None):
        """Initialize the image metadata extractor.

        Args:
            cache_manager: Optional cache manager for caching extraction results
        """
        super().__init__(cache_manager)
        self.mime_detector = MimeTypeDetector()

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
        Extract metadata from an image file.

        Args:
            file_path: Path to the image file
            content: Not used for image files
            mime_type: Optional MIME type of the file
            metadata: Optional existing metadata to enhance

        Returns:
            Dictionary containing extracted image metadata
        """
        path = Path(file_path)
        if not path.exists():
            logger.warning(f"Image file not found: {path}")
            return {}

        # Determine MIME type if not provided
        if mime_type is None:
            mime_type, _ = self.mime_detector.get_mime_type(path)

        # Check if this is a supported image type
        if mime_type not in self.SUPPORTED_MIME_TYPES:
            logger.debug(f"Unsupported image type: {mime_type} for file: {path}")
            return {}

        # Try to use cache if available
        if self.cache_manager:
            cache_key = f"image_metadata:{path}:{path.stat().st_mtime}"
            cached_data = await self.cache_manager.get(cache_key)
            if cached_data:
                logger.debug(f"Using cached image metadata for {path}")
                return cached_data

        # Process the image file
        try:
            result = await self._process_image(path)

            # Cache the result if cache manager is available
            if self.cache_manager:
                await self.cache_manager.put(cache_key, result)

            return result
        except Exception as e:
            logger.error(f"Error extracting image metadata from {path}: {str(e)}")
            return {}

    async def _process_image(self, path: Path) -> dict[str, Any]:
        """
        Process an image file to extract metadata.

        Args:
            path: Path to the image file

        Returns:
            Dictionary containing extracted image metadata
        """
        result = {"metadata_type": "image", "dimensions": {}, "exif": {}, "gps": {}}

        try:
            with Image.open(path) as img:
                # Basic image information
                result["format"] = img.format
                result["mode"] = img.mode
                result["dimensions"] = {
                    "width": img.width,
                    "height": img.height,
                    "aspect_ratio": round(img.width / img.height, 3)
                    if img.height > 0
                    else None,
                }

                # Get resolution if available
                if hasattr(img, "info") and "dpi" in img.info:
                    result["resolution"] = {
                        "dpi_x": img.info["dpi"][0],
                        "dpi_y": img.info["dpi"][1],
                    }

                # Get ICC profile information if available
                if "icc_profile" in img.info:
                    result["has_color_profile"] = True

                # Extract EXIF data if available
                exif_data = self._extract_exif(img)
                if exif_data:
                    result["exif"] = exif_data

                # Check for animation in GIFs - using safe attribute access
                if (
                    img.format == "GIF"
                    and hasattr(img, "is_animated")
                    and getattr(img, "is_animated", False)
                ):
                    # For animated GIFs, try to get frame count
                    frame_count = getattr(img, "n_frames", 0)
                    if frame_count > 0:
                        result["animation"] = {
                            "frame_count": frame_count,
                            "duration": img.info.get("duration", 0),
                        }

                # Extract transparency information
                if "transparency" in img.info:
                    result["has_transparency"] = True
                elif img.mode in ("RGBA", "LA"):
                    result["has_transparency"] = True

                # Check for thumbnail in JPEG
                if img.format == "JPEG" and hasattr(img, "_getexif"):
                    # Use safe method to get EXIF data
                    exif_info = self._safe_get_exif(img)
                    if exif_info and 40094 in exif_info:  # Embedded thumbnail tag
                        result["has_thumbnail"] = True

        except Exception as e:
            logger.error(f"Error processing image {path}: {str(e)}")

        return result

    def _safe_get_exif(self, img: Image.Image) -> dict[Any, Any] | None:
        """
        Safely get EXIF data from an image.

        Args:
            img: PIL Image object

        Returns:
            Dictionary containing EXIF data or None if unavailable
        """
        try:
            if hasattr(img, "_getexif"):
                exif_method = getattr(img, "_getexif", None)
                if callable(exif_method):
                    return exif_method()
            return None
        except Exception as e:
            logger.debug(f"Error getting EXIF data: {str(e)}")
            return None

    def _extract_exif(self, img: Image.Image) -> dict[str, Any]:
        """
        Extract EXIF metadata from an image.

        Args:
            img: PIL Image object

        Returns:
            Dictionary containing EXIF metadata
        """
        exif_data = {}
        gps_data = {}

        # First check if image has exif data
        exif_info = self._safe_get_exif(img)
        if exif_info:
            # Process standard EXIF tags
            for tag_id, value in exif_info.items():
                tag = TAGS.get(tag_id, str(tag_id))

                # Skip binary data and oversized tag values
                if isinstance(value, bytes) and len(value) > 100:
                    exif_data[tag] = f"Binary data ({len(value)} bytes)"
                    continue

                # Handle special tags
                if tag == "GPSInfo" and isinstance(value, dict):
                    for gps_tag_id, gps_value in value.items():
                        gps_tag = GPSTAGS.get(gps_tag_id, str(gps_tag_id))
                        gps_data[gps_tag] = gps_value
                else:
                    # Ensure the value is serializable
                    if isinstance(value, (int, float, str, bool, list, dict, tuple)):
                        exif_data[tag] = value
                    else:
                        exif_data[tag] = str(value)

        # Extract basic date/time info if available
        if "DateTime" in exif_data:
            exif_data["capture_datetime"] = exif_data["DateTime"]

        # Process camera information
        camera_info = {}
        if "Make" in exif_data:
            camera_info["make"] = exif_data["Make"]
        if "Model" in exif_data:
            camera_info["model"] = exif_data["Model"]
        if camera_info:
            exif_data["camera"] = camera_info

        # Process exposure information
        exposure_info = {}
        if "ExposureTime" in exif_data:
            exposure_info["exposure_time"] = exif_data["ExposureTime"]
        if "FNumber" in exif_data:
            exposure_info["f_number"] = exif_data["FNumber"]
        if "ISOSpeedRatings" in exif_data:
            exposure_info["iso"] = exif_data["ISOSpeedRatings"]
        if "ExposureProgram" in exif_data:
            exposure_info["program"] = exif_data["ExposureProgram"]
        if exposure_info:
            exif_data["exposure"] = exposure_info

        # Process lens information
        lens_info = {}
        if "LensMake" in exif_data:
            lens_info["make"] = exif_data["LensMake"]
        if "LensModel" in exif_data:
            lens_info["model"] = exif_data["LensModel"]
        if "FocalLength" in exif_data:
            lens_info["focal_length"] = exif_data["FocalLength"]
        if lens_info:
            exif_data["lens"] = lens_info

        # Format GPS data in a more useful way if it exists
        if gps_data:
            formatted_gps = self._format_gps_data(gps_data)
            if formatted_gps:
                exif_data["gps"] = formatted_gps

        return exif_data

    def _format_gps_data(self, gps_data: dict[str, Any]) -> dict[str, Any]:
        """
        Format GPS data into a more usable structure.

        Args:
            gps_data: Dictionary of raw GPS data from EXIF

        Returns:
            Dictionary with formatted GPS information
        """
        formatted_gps = {}

        # Extract latitude
        if "GPSLatitude" in gps_data and "GPSLatitudeRef" in gps_data:
            try:
                lat = self._convert_gps_coordinate(gps_data["GPSLatitude"])
                lat_ref = gps_data["GPSLatitudeRef"]
                if lat_ref == "S":
                    lat = -lat
                formatted_gps["latitude"] = lat
            except Exception as e:
                logger.debug(f"Error processing latitude: {str(e)}")

        # Extract longitude
        if "GPSLongitude" in gps_data and "GPSLongitudeRef" in gps_data:
            try:
                lon = self._convert_gps_coordinate(gps_data["GPSLongitude"])
                lon_ref = gps_data["GPSLongitudeRef"]
                if lon_ref == "W":
                    lon = -lon
                formatted_gps["longitude"] = lon
            except Exception as e:
                logger.debug(f"Error processing longitude: {str(e)}")

        # Extract altitude
        if "GPSAltitude" in gps_data and "GPSAltitudeRef" in gps_data:
            try:
                alt = float(gps_data["GPSAltitude"].numerator) / float(
                    gps_data["GPSAltitude"].denominator
                )
                alt_ref = gps_data["GPSAltitudeRef"]
                if alt_ref == 1:
                    alt = -alt
                formatted_gps["altitude"] = alt
            except Exception as e:
                logger.debug(f"Error processing altitude: {str(e)}")

        return formatted_gps

    def _convert_gps_coordinate(self, coordinate) -> float:
        """
        Convert GPS coordinates from the EXIF format to decimal degrees.

        Args:
            coordinate: GPS coordinate in EXIF format (degrees, minutes, seconds)

        Returns:
            Float representing the coordinate in decimal degrees
        """
        degrees = float(coordinate[0].numerator) / float(coordinate[0].denominator)
        minutes = float(coordinate[1].numerator) / float(coordinate[1].denominator)
        seconds = float(coordinate[2].numerator) / float(coordinate[2].denominator)

        return degrees + (minutes / 60.0) + (seconds / 3600.0)


# Register the extractor
MetadataExtractorRegistry.register(ImageMetadataExtractor)
