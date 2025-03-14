"""Generates and manages file tree representations."""

import logging
import os
from pathlib import Path
from typing import Dict

from backend.utils.cache_manager import cache_manager
from backend.utils.safety import SafeFileHandler

logger = logging.getLogger(__name__)


async def generate_file_tree(
    directory_path: Path,
    max_depth: int = 10,
    use_cache: bool = True,
    cache_ttl: int = 300,  # 5 minutes cache TTL
) -> Dict:
    """
    Generate a hierarchical representation of files and directories.

    Args:
        directory_path: Root directory to process
        max_depth: Maximum directory depth to traverse
        use_cache: Whether to use caching
        cache_ttl: Cache time-to-live in seconds

    Returns:
        Dict representation of the file tree
    """
    # Check cache first if enabled
    if use_cache:
        cache_key = f"file_tree_{str(directory_path)}_{max_depth}"
        cached_tree = await cache_manager.get(cache_key)
        if cached_tree:
            return cached_tree

    async def process_directory(path: Path, current_depth: int) -> Dict:
        """Process a directory and its contents recursively."""
        if current_depth > max_depth:
            return {"type": "directory", "truncated": True}

        try:
            result = {}

            # List directory contents
            try:
                entries = os.listdir(path)
            except PermissionError:
                logger.warning(f"Permission denied accessing directory: {path}")
                return {"type": "directory", "error": "permission_denied"}
            except Exception as e:
                logger.error(f"Error accessing directory {path}: {e}")
                return {"type": "directory", "error": str(e)}

            for entry in entries:
                entry_path = path / entry

                # Skip ignored files/directories
                if SafeFileHandler.should_ignore(entry_path):
                    continue

                try:
                    if entry_path.is_file():
                        # Get file metadata
                        try:
                            stats = entry_path.stat()
                            result[entry] = {
                                "type": "file",
                                "size": stats.st_size,
                                "modified": stats.st_mtime,
                                "created": stats.st_ctime,
                            }
                        except Exception as e:
                            logger.error(
                                f"Error getting file stats for {entry_path}: {e}"
                            )
                            result[entry] = {"type": "file", "error": str(e)}
                    elif entry_path.is_dir():
                        # Process subdirectory
                        result[entry] = await process_directory(
                            entry_path, current_depth + 1
                        )
                except Exception as e:
                    logger.error(f"Error processing {entry_path}: {e}")
                    result[entry] = {"type": "unknown", "error": str(e)}

            return result
        except Exception as e:
            logger.error(f"Error processing directory {path}: {e}")
            return {"type": "directory", "error": str(e)}

    # Generate the file tree
    try:
        tree = await process_directory(directory_path, 0)

        # Cache the result if caching is enabled
        if use_cache:
            cache_key = f"file_tree_{str(directory_path)}_{max_depth}"
            await cache_manager.put(cache_key, tree)

        return tree
    except Exception as e:
        logger.error(f"Error generating file tree for {directory_path}: {e}")
        return {"type": "directory", "error": str(e)}


async def invalidate_file_tree_cache(directory_path: Path) -> None:
    """
    Invalidate the file tree cache for a directory.

    Args:
        directory_path: Directory whose cache should be invalidated
    """
    try:
        await cache_manager.invalidate_pattern(f"file_tree_{str(directory_path)}")
    except Exception as e:
        logger.error(f"Error invalidating file tree cache for {directory_path}: {e}")


async def get_file_tree_stats(directory_path: Path) -> Dict:
    """
    Get statistics about a file tree.

    Args:
        directory_path: Root directory to analyze

    Returns:
        Dictionary containing file tree statistics
    """
    stats = {
        "total_files": 0,
        "total_dirs": 0,
        "total_size": 0,
        "max_depth": 0,
        "errors": [],
    }

    async def analyze_directory(path: Path, current_depth: int) -> None:
        nonlocal stats

        try:
            entries = os.listdir(path)

            for entry in entries:
                entry_path = path / entry

                if SafeFileHandler.should_ignore(entry_path):
                    continue

                try:
                    if entry_path.is_file():
                        stats["total_files"] += 1
                        stats["total_size"] += entry_path.stat().st_size
                    elif entry_path.is_dir():
                        stats["total_dirs"] += 1
                        stats["max_depth"] = max(stats["max_depth"], current_depth + 1)
                        await analyze_directory(entry_path, current_depth + 1)
                except Exception as e:
                    stats["errors"].append(str(e))
        except Exception as e:
            stats["errors"].append(str(e))

    await analyze_directory(directory_path, 0)
    return stats
