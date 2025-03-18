"""
Web ingest source implementation.

This module provides an ingest source that ingests content from web URLs.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import aiohttp

from ..models import ContentType, IngestContent, IngestSource
from .base_source import BaseIngestSource

logger = logging.getLogger(__name__)


class WebIngestSource(BaseIngestSource):
    """
    Ingest source that reads from web URLs.

    This source can ingest content from HTTP and HTTPS URLs with various
    options for authentication, headers, and content types.
    """

    def __init__(self):
        """Initialize the web ingest source."""
        self._session = None
        self._is_initialized = False

    @property
    def source_type(self) -> str:
        """Get the ingest source type identifier."""
        return "web"

    async def initialize(self) -> None:
        """Initialize the web ingest source."""
        if self._is_initialized:
            return

        # Create HTTP session
        self._session = aiohttp.ClientSession()

        self._is_initialized = True
        logger.info("Web ingest source initialized")

    async def close(self) -> None:
        """Close the web ingest source."""
        if not self._is_initialized:
            return

        # Close HTTP session
        if self._session:
            await self._session.close()
            self._session = None

        self._is_initialized = False
        logger.info("Web ingest source closed")

    async def validate_config(self, config: dict[str, Any]) -> bool:
        """
        Validate source configuration.

        Args:
            config: The configuration to validate

        Returns:
            True if configuration is valid, False otherwise
        """
        # Check if URLs are provided
        if "urls" not in config or not config["urls"]:
            logger.error("Missing required config parameter: urls")
            return False

        # Validate each URL
        for url in config["urls"]:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                logger.error(f"Invalid URL: {url}")
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
            "urls": [],
            "headers": {},
            "auth": None,
            "timeout": 30,
            "max_size_mb": 10,
            "follow_redirects": True,
            "verify_ssl": True,
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
        urls = config.get("urls", [])

        # For web sources, content is the URLs themselves
        result = []
        for url in urls:
            parsed = urlparse(url)
            path = parsed.path
            filename = Path(path).name if path else f"{parsed.netloc}.html"

            result.append(
                {
                    "id": url,
                    "url": url,
                    "filename": filename,
                    "host": parsed.netloc,
                    "path": path,
                    "scheme": parsed.scheme,
                    "content_type": self._guess_content_type(url).value,
                }
            )

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
            content_id: Optional URL to ingest
            options: Optional ingest-specific options

        Returns:
            List of ingested content items
        """
        self._ensure_initialized()

        # Get config
        config = source.config
        urls = config.get("urls", [])
        headers = config.get("headers", {})
        auth = config.get("auth")
        timeout = config.get("timeout", 30)
        max_size_mb = config.get("max_size_mb", 10)
        follow_redirects = config.get("follow_redirects", True)
        verify_ssl = config.get("verify_ssl", True)
        options = options or {}

        # Override with options if provided
        if "headers" in options:
            headers.update(options["headers"])
        if "auth" in options:
            auth = options["auth"]
        if "timeout" in options:
            timeout = options["timeout"]

        result = []

        # If content_id is provided, only ingest that URL
        urls_to_ingest = [content_id] if content_id else urls

        for url in urls_to_ingest:
            # Skip if URL is empty
            if not url:
                continue

            try:
                # Fetch URL
                async with self._session.get(
                    url,
                    headers=headers,
                    auth=aiohttp.BasicAuth(*auth) if auth else None,
                    timeout=timeout,
                    allow_redirects=follow_redirects,
                    ssl=None if verify_ssl else False,
                ) as response:
                    # Check response status
                    if response.status != 200:
                        logger.warning(
                            f"Failed to fetch URL {url}: HTTP {response.status}"
                        )
                        continue

                    # Check content type
                    content_type_header = response.headers.get("Content-Type", "")
                    content_type = self._parse_content_type(content_type_header)

                    # Check content length
                    content_length = int(response.headers.get("Content-Length", "0"))
                    if content_length > max_size_mb * 1024 * 1024:
                        logger.warning(
                            f"Content too large: {url} ({content_length} bytes)"
                        )
                        continue

                    # Read content
                    if content_type == ContentType.BINARY:
                        content = await response.read()
                    else:
                        content = await response.text()

                    # Create ingest content
                    parsed = urlparse(url)
                    path = parsed.path
                    filename = Path(path).name if path else f"{parsed.netloc}.html"

                    result.append(
                        IngestContent(
                            source_id=source.id,
                            content_type=content_type,
                            path=url,
                            filename=filename,
                            content=content,
                            metadata={
                                "url": url,
                                "host": parsed.netloc,
                                "status": response.status,
                                "headers": dict(response.headers),
                                "ingest_time": datetime.now().isoformat(),
                            },
                        )
                    )
            except Exception as e:
                logger.error(f"Error ingesting URL {url}: {e}")

        return result

    async def get_content_metadata(
        self, source: IngestSource, content_id: str
    ) -> dict[str, Any]:
        """
        Get metadata for a specific content item.

        Args:
            source: The source configuration
            content_id: URL of the content item

        Returns:
            Metadata dictionary
        """
        self._ensure_initialized()

        # Get config
        config = source.config
        headers = config.get("headers", {})
        auth = config.get("auth")
        timeout
