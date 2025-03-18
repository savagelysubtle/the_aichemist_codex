"""
Implementation of the metadata management service.

This module provides functionality for extracting and managing metadata
from different file types, addressing circular dependencies through the
registry pattern.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from ...core.exceptions import MetadataError
from ...core.interfaces import MetadataManager as MetadataManagerInterface
from ...core.models import FileMetadata
from ...registry import Registry


class MetadataManager(MetadataManagerInterface):
    """
    Metadata manager for extracting and managing file metadata.

    This class provides functionality for extracting and caching metadata
    from different file types, using the registry pattern to avoid circular
    dependencies.
    """

    def __init__(self):
        """Initialize the MetadataManager instance."""
        self._registry = Registry.get_instance()
        self._paths = self._registry.project_paths
        self._validator = self._registry.file_validator
        self._async_io = self._registry.async_io
        self._cache = self._registry.cache_manager

        # Cache directory for metadata
        self._metadata_dir = self._paths.get_cache_dir() / "metadata"
        os.makedirs(self._metadata_dir, exist_ok=True)

        # Set of supported file extensions (lowercase, without dots)
        self._supported_extensions: set[str] = {
            # Text files
            "txt",
            "md",
            "rst",
            "log",
            # Code files
            "py",
            "js",
            "html",
            "css",
            "json",
            "xml",
            "yaml",
            "yml",
            # Document files
            "pdf",
            "doc",
            "docx",
            "odt",
            "rtf",
            # Spreadsheet files
            "csv",
            "xls",
            "xlsx",
            "ods",
        }

    async def get_metadata(self, file_path: str) -> FileMetadata:
        """
        Get metadata for a file, either from cache or by extracting it.

        Args:
            file_path: Path to the file

        Returns:
            The file metadata

        Raises:
            MetadataError: If there is an error extracting the metadata
        """
        # Ensure the path is safe
        file_path = self._validator.ensure_path_safe(file_path)

        # Normalize the path
        path_obj = Path(file_path)

        # Check if file exists
        if not await self._async_io.file_exists(file_path):
            raise MetadataError(f"File not found: {file_path}", file_path)

        # Try to get metadata from cache
        cache_key = f"metadata:{file_path}"
        cached_metadata = await self._cache.get(cache_key)

        if cached_metadata is not None:
            return FileMetadata(**cached_metadata)

        # Extract metadata from file
        return await self._extract_and_cache_metadata(file_path, path_obj)

    async def _extract_and_cache_metadata(
        self, file_path: str, path_obj: Path
    ) -> FileMetadata:
        """
        Extract metadata from a file and cache it.

        Args:
            file_path: Path to the file
            path_obj: Path object for the file

        Returns:
            The extracted file metadata

        Raises:
            MetadataError: If there is an error extracting the metadata
        """
        try:
            # Get basic file information
            stat_result = path_obj.stat()
            filename = path_obj.name
            extension = path_obj.suffix.lower()[1:] if path_obj.suffix else ""

            # Create basic metadata
            metadata = FileMetadata(
                path=file_path,
                filename=filename,
                extension=extension,
                size=stat_result.st_size,
                created_time=datetime.fromtimestamp(stat_result.st_ctime),
                modified_time=datetime.fromtimestamp(stat_result.st_mtime),
                content_type=self._get_content_type(extension),
                keywords=[],
                description=None,
                title=None,
                author=None,
                extra_metadata={},
            )

            # Extract additional metadata based on file type
            if extension in self._supported_extensions:
                await self._extract_file_specific_metadata(
                    metadata, file_path, extension
                )

            # Cache the metadata
            cache_key = f"metadata:{file_path}"
            await self._cache.set(
                cache_key,
                metadata.__dict__,
                ttl=3600,  # Cache for 1 hour
            )

            return metadata

        except Exception as e:
            raise MetadataError(
                f"Error extracting metadata from file: {str(e)}", file_path
            )

    async def _extract_file_specific_metadata(
        self, metadata: FileMetadata, file_path: str, extension: str
    ) -> None:
        """
        Extract metadata specific to a file type.

        Args:
            metadata: The metadata object to update
            file_path: Path to the file
            extension: File extension
        """
        if extension in ("py", "js", "html", "css"):
            await self._extract_code_metadata(metadata, file_path)
        elif extension in ("txt", "md", "rst"):
            await self._extract_text_metadata(metadata, file_path)
        elif extension in ("json", "yaml", "yml"):
            await self._extract_data_metadata(metadata, file_path)

    async def _extract_code_metadata(
        self, metadata: FileMetadata, file_path: str
    ) -> None:
        """
        Extract metadata from code files.

        Args:
            metadata: The metadata object to update
            file_path: Path to the file
        """
        try:
            content = await self._async_io.read_file(file_path)
            lines = content.split("\n")

            # Look for module docstring
            docstring = ""
            in_docstring = False
            docstring_delimiter = '"""' if '"""' in content else "'''"

            for line in lines:
                line = line.strip()

                if not in_docstring and line.startswith(docstring_delimiter):
                    in_docstring = True
                    docstring = line.replace(docstring_delimiter, "")
                    if line.endswith(docstring_delimiter) and len(line) > 6:
                        # Single line docstring
                        docstring = docstring[:-3]
                        in_docstring = False
                elif in_docstring and docstring_delimiter in line:
                    # End of docstring
                    docstring += " " + line.split(docstring_delimiter)[0]
                    in_docstring = False
                elif in_docstring:
                    docstring += " " + line

            # Extract potential title and description from docstring
            if docstring:
                lines = docstring.strip().split("\n")
                metadata.title = lines[0].strip()
                if len(lines) > 1:
                    metadata.description = "\n".join(lines[1:]).strip()

            # Extract keywords (imports, functions, classes)
            keywords = set()

            for line in lines:
                line = line.strip()
                if line.startswith("import ") or line.startswith("from "):
                    # Extract import names
                    parts = line.split(" ")
                    if len(parts) > 1:
                        if parts[0] == "import":
                            keywords.add(parts[1].split(".")[0])
                        elif (
                            len(parts) > 3
                            and parts[0] == "from"
                            and parts[2] == "import"
                        ):
                            keywords.add(parts[1])
                elif line.startswith("def "):
                    # Extract function names
                    function_name = line.split("def ")[1].split("(")[0].strip()
                    keywords.add(function_name)
                elif line.startswith("class "):
                    # Extract class names
                    class_name = line.split("class ")[1].split("(")[0].strip(":")
                    keywords.add(class_name)

            # Update metadata
            metadata.keywords = list(keywords)

            # Count lines of code
            metadata.extra_metadata["lines_of_code"] = len(lines)
            metadata.extra_metadata["blank_lines"] = len(
                [line for line in lines if not line.strip()]
            )
            metadata.extra_metadata["comment_lines"] = len(
                [
                    line
                    for line in lines
                    if line.strip().startswith("#") or line.strip().startswith("//")
                ]
            )

        except Exception as e:
            # Log the error but don't raise since this is just enhanced metadata
            print(f"Error extracting code metadata: {str(e)}")

    async def _extract_text_metadata(
        self, metadata: FileMetadata, file_path: str
    ) -> None:
        """
        Extract metadata from text files.

        Args:
            metadata: The metadata object to update
            file_path: Path to the file
        """
        try:
            content = await self._async_io.read_file(file_path)
            lines = content.split("\n")

            # Use first line as title if it's not too long
            if lines and len(lines[0].strip()) <= 100:
                metadata.title = lines[0].strip()

            # Use next few lines as description
            if len(lines) > 1:
                description_lines = []
                for line in lines[1:6]:  # Consider up to 5 lines after the title
                    if line.strip():
                        description_lines.append(line.strip())
                if description_lines:
                    metadata.description = "\n".join(description_lines)

            # Extract potential keywords from the content
            words = " ".join(lines).split()
            word_count = {}
            for word in words:
                # Only consider words longer than 3 characters
                if len(word) > 3:
                    word = word.lower().strip(".,;:!?()[]{}'\"`")
                    if word:
                        word_count[word] = word_count.get(word, 0) + 1

            # Get the top 10 most frequent words as keywords
            sorted_words = sorted(word_count.items(), key=lambda x: x[1], reverse=True)
            metadata.keywords = [word for word, _ in sorted_words[:10]]

            # Update extra metadata
            metadata.extra_metadata["line_count"] = len(lines)
            metadata.extra_metadata["word_count"] = len(words)
            metadata.extra_metadata["char_count"] = len(content)

        except Exception as e:
            # Log the error but don't raise since this is just enhanced metadata
            print(f"Error extracting text metadata: {str(e)}")

    async def _extract_data_metadata(
        self, metadata: FileMetadata, file_path: str
    ) -> None:
        """
        Extract metadata from data files (JSON, YAML).

        Args:
            metadata: The metadata object to update
            file_path: Path to the file
        """
        try:
            content = await self._async_io.read_file(file_path)

            # For JSON files, extract structure information
            if metadata.extension == "json":
                try:
                    data = json.loads(content)
                    metadata.extra_metadata["json_structure"] = (
                        self._describe_data_structure(data)
                    )

                    # Try to extract top-level keys as keywords
                    if isinstance(data, dict):
                        metadata.keywords = list(data.keys())[:10]  # Limit to 10 keys
                except json.JSONDecodeError:
                    metadata.extra_metadata["json_valid"] = False

            # Record basic statistics
            metadata.extra_metadata["line_count"] = len(content.split("\n"))
            metadata.extra_metadata["char_count"] = len(content)

        except Exception as e:
            # Log the error but don't raise since this is just enhanced metadata
            print(f"Error extracting data metadata: {str(e)}")

    def _describe_data_structure(self, data: Any) -> str:
        """
        Generate a simple description of a data structure.

        Args:
            data: The data to describe

        Returns:
            A string describing the data structure
        """
        if isinstance(data, dict):
            if not data:
                return "empty object"
            keys = list(data.keys())
            sample_keys = keys[:3]
            return f"object with {len(keys)} keys: {', '.join(sample_keys)}" + (
                "..." if len(keys) > 3 else ""
            )
        elif isinstance(data, list):
            if not data:
                return "empty array"
            return f"array with {len(data)} items"
        elif isinstance(data, str):
            return "string"
        elif isinstance(data, (int, float)):
            return "number"
        elif isinstance(data, bool):
            return "boolean"
        elif data is None:
            return "null"
        else:
            return str(type(data).__name__)

    def _get_content_type(self, extension: str) -> str:
        """
        Get the content type (MIME type) based on the file extension.

        Args:
            extension: File extension without the leading dot

        Returns:
            The content type
        """
        # Map of file extensions to MIME types
        mime_types = {
            # Text files
            "txt": "text/plain",
            "md": "text/markdown",
            "rst": "text/x-rst",
            "log": "text/plain",
            # Code files
            "py": "text/x-python",
            "js": "application/javascript",
            "html": "text/html",
            "css": "text/css",
            "json": "application/json",
            "xml": "application/xml",
            "yaml": "application/x-yaml",
            "yml": "application/x-yaml",
            # Document files
            "pdf": "application/pdf",
            "doc": "application/msword",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "odt": "application/vnd.oasis.opendocument.text",
            "rtf": "application/rtf",
            # Spreadsheet files
            "csv": "text/csv",
            "xls": "application/vnd.ms-excel",
            "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "ods": "application/vnd.oasis.opendocument.spreadsheet",
            # Image files
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "png": "image/png",
            "gif": "image/gif",
            "svg": "image/svg+xml",
            "webp": "image/webp",
            # Audio files
            "mp3": "audio/mpeg",
            "wav": "audio/wav",
            "ogg": "audio/ogg",
            "flac": "audio/flac",
            # Video files
            "mp4": "video/mp4",
            "avi": "video/x-msvideo",
            "mov": "video/quicktime",
            "webm": "video/webm",
        }

        return mime_types.get(extension.lower(), "application/octet-stream")

    async def update_metadata(
        self, file_path: str, updates: dict[str, Any]
    ) -> FileMetadata:
        """
        Update metadata for a file.

        Args:
            file_path: Path to the file
            updates: Dictionary of metadata fields to update

        Returns:
            The updated metadata

        Raises:
            MetadataError: If there is an error updating the metadata
        """
        # Get current metadata
        metadata = await self.get_metadata(file_path)

        # Update fields
        for key, value in updates.items():
            if hasattr(metadata, key):
                setattr(metadata, key, value)
            elif key.startswith("extra_"):
                # Allow updating nested fields in extra_metadata
                nested_key = key[6:]  # Remove "extra_" prefix
                metadata.extra_metadata[nested_key] = value
            else:
                # Add to extra_metadata
                metadata.extra_metadata[key] = value

        # Save to cache
        cache_key = f"metadata:{file_path}"
        await self._cache.set(
            cache_key,
            metadata.__dict__,
            ttl=3600,  # Cache for 1 hour
        )

        return metadata

    async def search_metadata(
        self, query: str, file_extensions: list[str] = None, limit: int = 10
    ) -> list[FileMetadata]:
        """
        Search for files by metadata.

        Args:
            query: Search query
            file_extensions: Filter by file extensions
            limit: Maximum number of results

        Returns:
            List of matching file metadata
        """
        results = []
        query = query.lower()

        # Get all metadata cache files
        metadata_files = list(self._metadata_dir.glob("*.json"))

        for metadata_file in metadata_files[
            : limit * 10
        ]:  # Process more files than limit to ensure we find enough matches
            try:
                with open(metadata_file) as f:
                    data = json.load(f)

                metadata = FileMetadata(**data)

                # Apply file extension filter
                if file_extensions and metadata.extension not in file_extensions:
                    continue

                # Search in various metadata fields
                if (
                    query in metadata.path.lower()
                    or query in metadata.filename.lower()
                    or (metadata.title and query in metadata.title.lower())
                    or (metadata.description and query in metadata.description.lower())
                    or query in " ".join(metadata.keywords).lower()
                ):
                    results.append(metadata)
                    if len(results) >= limit:
                        break
            except Exception:
                # Skip files with errors
                continue

        return results
