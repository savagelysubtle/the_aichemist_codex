"""Cache management utilities for The AIchemist Codex."""

import asyncio
import json
import logging
import time
from pathlib import Path

logger = logging.getLogger(__name__)


class MemoryCache:
    """In-memory LRU cache implementation."""

    def __init__(self, max_items: int = 1000, ttl: int = 3600) -> None:
        """
        Initialize memory cache with max size and TTL.

        Args:
            max_items: Maximum number of items to store
            ttl: Time-to-live in seconds (default: 1 hour)
        """
        self.max_items = max_items
        self.ttl = ttl
        self._cache: dict[str, object] = {}
        self._access_times: dict[str, float] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> object | None:
        """
        Get item from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found or expired
        """
        async with self._lock:
            if key not in self._cache:
                return None

            # Check if item is expired
            timestamp = self._access_times.get(key, 0)
            if self.ttl > 0 and time.time() - timestamp > self.ttl:
                # Remove expired item
                del self._cache[key]
                del self._access_times[key]
                return None

            # Update access time
            self._access_times[key] = time.time()
            return self._cache[key]

    async def put(self, key: str, value: object) -> None:
        """
        Add item to cache.

        Args:
            key: Cache key
            value: Value to cache
        """
        async with self._lock:
            # Make room if necessary
            if len(self._cache) >= self.max_items and key not in self._cache:
                self._evict_lru_item()

            # Store item
            self._cache[key] = value
            self._access_times[key] = time.time()

    def _evict_lru_item(self) -> None:
        """Remove least recently used item from cache."""
        if not self._access_times:
            return

        # Find oldest item
        oldest_key = min(self._access_times.items(), key=lambda x: x[1])[0]
        del self._cache[oldest_key]
        del self._access_times[oldest_key]

    async def invalidate(self, key: str) -> None:
        """
        Remove item from cache.

        Args:
            key: Cache key to remove
        """
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                del self._access_times[key]

    async def clear(self) -> None:
        """Clear all items from cache."""
        async with self._lock:
            self._cache.clear()
            self._access_times.clear()

    async def get_stats(self) -> dict[str, object]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        async with self._lock:
            return {
                "size": len(self._cache),
                "max_size": self.max_items,
                "ttl": self.ttl,
                "oldest_item_age": time.time() - min(self._access_times.values())
                if self._access_times
                else 0,
                "newest_item_age": time.time() - max(self._access_times.values())
                if self._access_times
                else 0,
            }


class CacheManager:
    """Manages multiple caching mechanisms for the application."""

    def __init__(self, data_dir: Path | None = None, ttl: int = 3600) -> None:
        """
        Initialize the cache manager.

        Args:
            data_dir: Directory for persistent cache storage
            ttl: Default TTL in seconds for cached items
        """
        self.data_dir = data_dir
        self.ttl = ttl
        self.memory_cache = MemoryCache(ttl=ttl)

        # Create cache directory if it doesn't exist
        if self.data_dir:
            self.data_dir.mkdir(parents=True, exist_ok=True)

    async def get(self, key: str) -> object | None:
        """
        Get item from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        # Try memory cache first
        value = await self.memory_cache.get(key)
        if value is not None:
            return value

        # Try disk cache if available
        if self.data_dir:
            disk_value = await self._get_from_disk(key)
            if disk_value is not None:
                # Store in memory cache for faster access next time
                await self.memory_cache.put(key, disk_value)
            return disk_value

        return None

    async def put(self, key: str, value: object, ttl: int | None = None) -> None:
        """
        Store item in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Optional custom TTL in seconds
        """
        # Store in memory cache
        await self.memory_cache.put(key, value)

        # Also store in disk cache if available
        if self.data_dir:
            await self._store_to_disk(key, value, ttl or self.ttl)

    async def invalidate(self, key: str) -> None:
        """
        Remove item from all caches.

        Args:
            key: Cache key to remove
        """
        # Remove from memory cache
        await self.memory_cache.invalidate(key)

        # Remove from disk cache if available
        if self.data_dir:
            await self._remove_from_disk(key)

    async def clear(self) -> None:
        """Clear all caches."""
        # Clear memory cache
        await self.memory_cache.clear()

        # Clear disk cache if available
        if self.data_dir:
            for cache_file in self.data_dir.glob("*.cache"):
                try:
                    cache_file.unlink()
                except Exception as e:
                    logger.error(f"Error removing cache file {cache_file}: {e}")

    async def _get_from_disk(self, key: str) -> object | None:
        """
        Get item from disk cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found or expired
        """
        if not self.data_dir:
            return None

        try:
            cache_file = self.data_dir / f"{key}.cache"
            if not cache_file.exists():
                return None

            with open(cache_file) as f:
                cache_data = json.load(f)

            # Check if expired
            if "expiry" in cache_data and cache_data["expiry"] < time.time():
                # Remove expired file
                cache_file.unlink()
                return None

            return cache_data["value"]
        except Exception as e:
            logger.error(f"Error reading from disk cache for key {key}: {e}")
            return None

    async def _store_to_disk(self, key: str, value: object, ttl: int) -> None:
        """
        Store item in disk cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: TTL in seconds
        """
        if not self.data_dir:
            return

        try:
            cache_file = self.data_dir / f"{key}.cache"

            # Create cache data with expiry
            cache_data = {
                "value": value,
                "expiry": time.time() + ttl,
                "created_at": time.time(),
            }

            # Write to file
            with open(cache_file, "w") as f:
                json.dump(cache_data, f)
        except Exception as e:
            logger.error(f"Error writing to disk cache for key {key}: {e}")

    async def _remove_from_disk(self, key: str) -> None:
        """
        Remove item from disk cache.

        Args:
            key: Cache key to remove
        """
        if not self.data_dir:
            return

        try:
            cache_file = self.data_dir / f"{key}.cache"
            if cache_file.exists():
                cache_file.unlink()
        except Exception as e:
            logger.error(f"Error removing from disk cache for key {key}: {e}")
