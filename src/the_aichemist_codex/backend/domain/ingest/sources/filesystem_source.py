"""
Filesystem ingest source implementation.

This module provides an ingest source that reads from the local filesystem.
"""

import fnmatch
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from ....registry import Registry
from ..models import ContentType, IngestContent, IngestSource
from .base_source import BaseIngestSource

logger = logging.getLogger(__name__)


class FilesystemIngestSource(BaseIngestSource):
    """
    Ingest source that reads from the local filesystem.

    This source can ingest files from directories with pattern matching
    and exclusion filters.
    """

    def __init__(self):
        """Initialize the filesystem ingest source."""
        self._registry = Registry.get_instance()
        self._is_initialized = False

    @property
    def source_type(self) -> str:
        """Get the ingest source type identifier."""
        return "filesystem"

    async def initialize(self) -> None:
        """Initialize the filesystem ingest source."""
        if self._is_initialized:
            return

        self._is_initialized = True
        logger.info("Filesystem ingest source initialized")

    async def close(self) -> None:
        """Close the filesystem ingest source."""
        if not self._is_initialized:
            return

        self._is_initialized = False
        logger.info("Filesystem ingest source closed")

    async def validate_config(self, config: dict[str, Any]) -> bool:
        """
        Validate source configuration.

        Args:
            config: The configuration to validate

        Returns:
            True if configuration is valid, False otherwise
        """
        # Check if base_path is provided
        if "base_path" not in config:
            logger.error("Missing required config parameter: base_path")
            return False

        base_path = Path(config["base_path"])

        # Check if base_path exists
        if not base_path.exists():
            logger.error(f"Base path does not exist: {base_path}")
            return False

        # Validation passed
        return True

    def get_default_config(self) -> dict[str, Any]:
        """
        Get default configuration for this source.

        Returns:
            Default configuration dictionary
        """
        return {
            "base_path": str(Path.home()),
            "patterns": ["*"],
            "exclude_patterns": [".git/*", "__pycache__/*", "*.pyc", "*.class"],
            "max_depth": 5,
            "max_file_size_mb": 10,
            "follow_symlinks": False,
            "include_hidden": False,
        }

    async def list_content(self, source: IngestSource) -> list[dict[str, Any]]:
        """
        List available content in the source.

        Args:
            source: The source configuration

        Returns:
            List of content items as dictionaries with metadata
        """
        self._ensure_initialized()

        # Get config
        config = source.config
        base_path = Path(config["base_path"])
        patterns = config.get("patterns", ["*"])
        exclude_patterns = config.get("exclude_patterns", [])
        max_depth = config.get("max_depth", 5)
        include_hidden = config.get("include_hidden", False)

        result = []

        # Walk through directory
        for root, dirs, files in os.walk(str(base_path)):
            # Calculate current depth
            current_path = Path(root)
            rel_path = current_path.relative_to(base_path)
            depth = len(rel_path.parts)

            # Skip if too deep
            if depth > max_depth:
                dirs.clear()  # Don't descend further
                continue

            # Skip hidden directories if not including them
            if not include_hidden:
                dirs[:] = [d for d in dirs if not d.startswith(".")]

            # Process files
            for file in files:
                file_path = Path(root) / file
                rel_file_path = file_path.relative_to(base_path)

                # Skip hidden files if not including them
                if not include_hidden and file.startswith("."):
                    continue

                # Check if file matches any pattern
                match = False
                for pattern in patterns:
                    if fnmatch.fnmatch(str(rel_file_path), pattern):
                        match = True
                        break

                if not match:
                    continue

                # Check if file matches any exclude pattern
                excluded = False
                for pattern in exclude_patterns:
                    if fnmatch.fnmatch(str(rel_file_path), pattern):
                        excluded = True
                        break

                if excluded:
                    continue

                # Get file metadata
                try:
                    stat = file_path.stat()
                    size = stat.st_size
                    mtime = stat.st_mtime

                    result.append(
                        {
                            "id": str(rel_file_path),
                            "path": str(file_path),
                            "rel_path": str(rel_file_path),
                            "name": file,
                            "size": size,
                            "size_mb": round(size / (1024 * 1024), 2),
                            "modified": datetime.fromtimestamp(mtime).isoformat(),
                            "content_type": ContentType.from_extension(
                                file_path.suffix
                            ).value,
                        }
                    )
                except Exception as e:
                    logger.warning(f"Error getting metadata for {file_path}: {e}")

        return result

    async def ingest_content(
        self,
        source: IngestSource,
        content_id: str | None = None,
        options: dict[str, Any] | None = None,
    ) -> list[IngestContent]:
        """
        Ingest content from the source.

        Args:
            source: The source configuration
            content_id: Optional ID of specific content to ingest (relative path)
            options: Optional ingest-specific options

        Returns:
            List of ingested content items
        """
        self._ensure_initialized()

        # Get config
        config = source.config
        base_path = Path(config["base_path"])
        max_file_size_mb = config.get("max_file_size_mb", 10)
        max_file_size_bytes = max_file_size_mb * 1024 * 1024
        options = options or {}

        result = []

        # If content_id is provided, only ingest that file
        if content_id:
            file_path = base_path / content_id
            if not file_path.exists() or not file_path.is_file():
                logger.error(f"File not found: {file_path}")
                return []

            # Check file size
            size = file_path.stat().st_size
            if size > max_file_size_bytes:
                logger.warning(f"File too large: {file_path} ({size} bytes)")
                return []

            # Ingest file
            try:
                result.append(
                    self._ingest_file(file_path, source.id, content_id, options)
                )
            except Exception as e:
                logger.error(f"Error ingesting file {file_path}: {e}")
        else:
            # Ingest all matching files
            content_list = await self.list_content(source)

            for content_item in content_list:
                file_path = Path(content_item["path"])
                rel_path = content_item["rel_path"]

                # Check file size
                size = content_item["size"]
                if size > max_file_size_bytes:
                    logger.warning(f"File too large: {file_path} ({size} bytes)")
                    continue

                # Ingest file
                try:
                    result.append(
                        self._ingest_file(file_path, source.id, rel_path, options)
                    )
                except Exception as e:
                    logger.error(f"Error ingesting file {file_path}: {e}")

        return result

    async def get_content_metadata(
        self, source: IngestSource, content_id: str
    ) -> dict[str, Any]:
        """
        Get metadata for a specific content item.

        Args:
            source: The source configuration
            content_id: ID of the content item (relative path)

        Returns:
            Metadata dictionary
        """
        self._ensure_initialized()

        # Get config
        config = source.config
        base_path = Path(config["base_path"])

        # Get file path
        file_path = base_path / content_id

        # Check if file exists
        if not file_path.exists() or not file_path.is_file():
            return {"error": "File not found"}

        # Get file metadata
        try:
            stat = file_path.stat()

            return {
                "id": content_id,
                "path": str(file_path),
                "name": file_path.name,
                "size": stat.st_size,
                "size_mb": round(stat.st_size / (1024 * 1024), 2),
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "accessed": datetime.fromtimestamp(stat.st_atime).isoformat(),
                "extension": file_path.suffix,
                "content_type": ContentType.from_extension(file_path.suffix).value,
            }
        except Exception as e:
            logger.error(f"Error getting metadata for {file_path}: {e}")
            return {"error": str(e)}

    def _ingest_file(
        self, file_path: Path, source_id: str, content_id: str, options: dict[str, Any]
    ) -> IngestContent:
        """
        Ingest a single file.

        Args:
            file_path: Path to the file
            source_id: ID of the source
            content_id: ID of the content (relative path)
            options: Ingest options

        Returns:
            Ingested content
        """
        # Determine content type
        content_type = ContentType.from_extension(file_path.suffix)

        # Read file content
        binary_mode = options.get("binary_mode", False)
        if binary_mode or content_type == ContentType.BINARY:
            with open(file_path, "rb") as f:
                content = f.read()
        else:
            encoding = options.get("encoding", "utf-8")
            try:
                with open(file_path, encoding=encoding) as f:
                    content = f.read()
            except UnicodeDecodeError:
                # If text reading fails, try binary
                with open(file_path, "rb") as f:
                    content = f.read()
                content_type = ContentType.BINARY

        # Get file metadata
        stat = file_path.stat()

        # Create ingest content
        return IngestContent(
            source_id=source_id,
            content_type=content_type,
            path=str(file_path),
            filename=file_path.name,
            content=content,
            metadata={
                "id": content_id,
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "extension": file_path.suffix,
            },
        )

    def _ensure_initialized(self) -> None:
        """
        Ensure that the source is initialized.

        Raises:
            RuntimeError: If not initialized
        """
        if not self._is_initialized:
            raise RuntimeError("Filesystem ingest source is not initialized")
