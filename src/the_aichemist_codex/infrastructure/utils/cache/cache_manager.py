"""Provides caching capabilities for performance optimization."""

import logging
import os
import re
import time
from collections import OrderedDict
from pathlib import Path
from typing import Any

from the_aichemist_codex.infrastructure.utils.io.async_io import AsyncFileIO

logger = logging.getLogger(__name__)


def get_cache_dir() -> Path:
    """
    Get the cache directory path dynamically to avoid circular imports.

    Returns:
        Path: The cache directory path
    """
    # Check for environment variable first
    env_cache_dir = os.environ.get("AICHEMIST_CACHE_DIR")
    if env_cache_dir:
        return Path(env_cache_dir).resolve()

    # Check for environment variable for data directory
    env_data_dir = os.environ.get("AICHEMIST_DATA_DIR")
    if env_data_dir:
        data_dir = Path(env_data_dir).resolve()
        return data_dir / "cache"

    # Fallback to a relative path from the current file
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent.parent
    return project_root / "data" / "cache"


class LRUCache:
    """Limited size in-memory LRU cache implementation."""

    def __init__(self, max_size: int = 1000):
        """Initialize LRU cache with maximum size."""
        self.cache: OrderedDict[str, Any] = OrderedDict()
        self.max_size = max_size

    def get(self, key: str) -> Any | None:
        """Get value from cache, moving item to end (most recently used)."""
        if key not in self.cache:
            return None

        # Move to end (mark as recently used)
        self.cache.move_to_end(key)
        return self.cache[key]

    def put(self, key: str, value: Any) -> None:
        """Add or update value in cache, evicting oldest item if full."""
        # If already exists, update and move to end
        if key in self.cache:
            self.cache.move_to_end(key)
            self.cache[key] = value
            return

        # Add new item
        self.cache[key] = value

        # Evict oldest item if needed
        if len(self.cache) > self.max_size:
            self.cache.popitem(last=False)


class CacheManager:
    """Manages both in-memory and disk-based caching."""

    def __init__(
        self,
        cache_dir: Path | None = None,
        memory_cache_size: int = 1000,
        disk_cache_ttl: int = 3600,
    ):  # 1 hour TTL by default
        """Initialize the cache manager with both memory and disk caches."""
        # Use the provided cache_dir or get it dynamically
        self.cache_dir = cache_dir if cache_dir is not None else get_cache_dir()

        # Ensure the cache directory exists
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.memory_cache = LRUCache(max_size=memory_cache_size)
        self.disk_cache_ttl = disk_cache_ttl
        self.async_io = AsyncFileIO()

        logger.debug(f"Cache manager initialized with directory: {self.cache_dir}")

    @staticmethod
    def sanitize_key(key: str) -> str:
        """
        Sanitize cache key to ensure it can be used as a filename.

        Replaces invalid characters with underscores.

        Args:
            key: The original cache key

        Returns:
            Sanitized key safe for use in filenames
        """
        # Replace characters that are illegal in filenames
        # This includes: <, >, :, ", /, \, |, ?, and *
        sanitized = re.sub(r'[<>:"/\\|?*]', "_", key)

        # Limit maximum length to avoid overly long filenames
        if len(sanitized) > 200:
            # Keep the beginning and end, replacing the middle with a hash
            import hashlib

            middle_hash = hashlib.md5(key.encode()).hexdigest()[:8]
            sanitized = sanitized[:95] + "_" + middle_hash + "_" + sanitized[-95:]

        return sanitized

    async def get(self, key: str) -> Any | None:
        """
        Get item from cache (memory first, then disk).

        Args:
            key: Cache key to retrieve

        Returns:
            Cached item or None if not found or expired
        """
        # Try memory cache first
        memory_result = self.memory_cache.get(key)
        if memory_result is not None:
            return memory_result

        # Try disk cache
        sanitized_key = self.sanitize_key(key)
        cache_file = self.cache_dir / f"{sanitized_key}.json"
        if await self.async_io.exists(cache_file):
            try:
                # Check if cache entry is expired
                stats = os.stat(cache_file)
                if time.time() - stats.st_mtime > self.disk_cache_ttl:
                    await self.invalidate(key)
                    return None

                data = await self.async_io.read_json(cache_file)
                if data:
                    # Update memory cache
                    self.memory_cache.put(key, data)
                    return data
            except Exception as e:
                logger.error(f"Error reading cache file {cache_file}: {e}")

        return None

    async def put(self, key: str, value: Any) -> bool:
        """
        Store item in both memory and disk cache.

        Args:
            key: Cache key
            value: Data to cache (must be JSON serializable)

        Returns:
            True if successful, False otherwise
        """
        try:
            # Update memory cache
            self.memory_cache.put(key, value)

            # Update disk cache with sanitized key
            sanitized_key = self.sanitize_key(key)
            cache_file = self.cache_dir / f"{sanitized_key}.json"
            return await self.async_io.write_json(cache_file, value)
        except Exception as e:
            logger.error(f"Error writing to cache for key {key}: {e}")
            return False

    async def invalidate(self, key: str) -> None:
        """
        Remove item from both memory and disk cache.

        Args:
            key: Cache key to invalidate
        """
        # Remove from memory cache
        if key in self.memory_cache.cache:
            del self.memory_cache.cache[key]

        # Remove from disk cache with sanitized key
        sanitized_key = self.sanitize_key(key)
        cache_file = self.cache_dir / f"{sanitized_key}.json"
        if await self.async_io.exists(cache_file):
            try:
                os.remove(cache_file)
            except Exception as e:
                logger.error(f"Error removing cache file {cache_file}: {e}")

    async def invalidate_pattern(self, pattern: str) -> None:
        """
        Remove all cache entries matching a pattern.

        Args:
            pattern: Pattern to match against cache keys
        """
        # Remove from memory cache
        keys_to_remove = [
            key for key in self.memory_cache.cache.keys() if pattern in key
        ]
        for key in keys_to_remove:
            del self.memory_cache.cache[key]

        # Remove from disk cache - use sanitized pattern
        sanitized_pattern = self.sanitize_key(pattern)
        try:
            for cache_file in self.cache_dir.glob(f"*{sanitized_pattern}*.json"):
                try:
                    os.remove(cache_file)
                except Exception as e:
                    logger.error(f"Error removing cache file {cache_file}: {e}")
        except Exception as e:
            logger.error(f"Error removing cache files matching pattern {pattern}: {e}")

    async def clear(self) -> None:
        """Clear all cache entries from both memory and disk."""
        # Clear memory cache
        self.memory_cache.cache.clear()

        # Clear disk cache
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                try:
                    os.remove(cache_file)
                except Exception as e:
                    logger.error(f"Error removing cache file {cache_file}: {e}")
        except Exception as e:
            logger.error(f"Error clearing disk cache: {e}")

    async def get_stats(self) -> dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary containing cache statistics
        """
        disk_cache_size = 0
        disk_cache_count = 0
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                disk_cache_size += os.path.getsize(cache_file)
                disk_cache_count += 1
        except Exception as e:
            logger.error(f"Error calculating disk cache stats: {e}")

        return {
            "memory_cache_size": len(self.memory_cache.cache),
            "memory_cache_max_size": self.memory_cache.max_size,
            "disk_cache_size_bytes": disk_cache_size,
            "disk_cache_count": disk_cache_count,
            "disk_cache_ttl": self.disk_cache_ttl,
        }


# Create a singleton instance for application-wide use
cache_manager = CacheManager()
