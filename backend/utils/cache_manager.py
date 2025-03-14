"""Provides caching capabilities for performance optimization."""

import logging
import os
import time
from collections import OrderedDict
from pathlib import Path
from typing import Any, Dict, Optional

from backend.config.settings import CACHE_DIR
from backend.utils.async_io import AsyncFileIO

logger = logging.getLogger(__name__)


class LRUCache:
    """Limited size in-memory LRU cache implementation."""

    def __init__(self, max_size: int = 1000):
        """Initialize LRU cache with maximum size."""
        self.cache = OrderedDict()
        self.max_size = max_size

    def get(self, key: str) -> Optional[Any]:
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
    """Manages in-memory and disk-based caching for file metadata."""

    def __init__(
        self,
        cache_dir: Path = CACHE_DIR,
        memory_cache_size: int = 1000,
        disk_cache_ttl: int = 3600,
    ):  # 1 hour TTL by default
        """
        Initialize the cache manager.

        Args:
            cache_dir: Directory to store disk cache files
            memory_cache_size: Maximum number of items in memory cache
            disk_cache_ttl: Time-to-live for disk cache entries in seconds
        """
        self.cache_dir = cache_dir
        self.memory_cache = LRUCache(max_size=memory_cache_size)
        self.disk_cache_ttl = disk_cache_ttl
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    async def get(self, key: str) -> Optional[Any]:
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
        cache_file = self.cache_dir / f"{key}.json"
        if await AsyncFileIO.exists(cache_file):
            try:
                # Check if cache entry is expired
                stats = os.stat(cache_file)
                if time.time() - stats.st_mtime > self.disk_cache_ttl:
                    await self.invalidate(key)
                    return None

                data = await AsyncFileIO.read_json(cache_file)
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

            # Update disk cache
            cache_file = self.cache_dir / f"{key}.json"
            return await AsyncFileIO.write_json(cache_file, value)
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

        # Remove from disk cache
        cache_file = self.cache_dir / f"{key}.json"
        if await AsyncFileIO.exists(cache_file):
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

        # Remove from disk cache
        try:
            for cache_file in self.cache_dir.glob(f"*{pattern}*.json"):
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

    async def get_stats(self) -> Dict[str, Any]:
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
