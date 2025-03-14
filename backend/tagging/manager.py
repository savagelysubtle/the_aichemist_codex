"""
Tag management system for file organization.

This module provides the TagManager class, which is responsible for
managing file tags, including creating, retrieving, updating, and
deleting tags and their associations with files.
"""

import logging
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import aiosqlite

from .schema import TagSchema

logger = logging.getLogger(__name__)


class TagManager:
    """
    Manages file tagging operations.

    This class provides methods for creating, retrieving, updating, and
    deleting tags and their associations with files. It also provides
    methods for querying files by tags and retrieving tag statistics.
    """

    def __init__(self, db_path: Path):
        """
        Initialize the TagManager with a database path.

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self.schema = TagSchema(db_path)
        self._db = None

    async def initialize(self) -> None:
        """
        Initialize the tag manager and create database tables if needed.

        Raises:
            sqlite3.Error: If initialization fails
        """
        await self.schema.initialize()
        self._db = await aiosqlite.connect(str(self.db_path))
        self._db.row_factory = sqlite3.Row
        await self._db.execute("PRAGMA foreign_keys = ON")
        logger.info("Initialized TagManager")

    async def close(self) -> None:
        """Close the database connection."""
        if self._db:
            await self._db.close()
            self._db = None
        self.schema.close()
        logger.debug("Closed TagManager")

    async def __aenter__(self) -> "TagManager":
        """Support for async context manager."""
        if not self._db:
            await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Support for async context manager."""
        await self.close()

    # Tag CRUD operations

    async def create_tag(self, name: str, description: Optional[str] = None) -> int:
        """
        Create a new tag.

        Args:
            name: Tag name
            description: Optional tag description

        Returns:
            int: ID of the created tag

        Raises:
            sqlite3.IntegrityError: If a tag with the same name already exists
            ValueError: If the tag name is empty
        """
        if not name or not name.strip():
            raise ValueError("Tag name cannot be empty")

        name = name.strip().lower()

        try:
            async with self._db.execute(
                "INSERT INTO tags (name, description) VALUES (?, ?)",
                (name, description),
            ) as cursor:
                tag_id = cursor.lastrowid
                await self._db.commit()
                logger.debug(f"Created tag: {name} (ID: {tag_id})")
                return tag_id
        except sqlite3.IntegrityError:
            logger.warning(f"Tag already exists: {name}")
            raise

    async def get_tag(self, tag_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a tag by ID.

        Args:
            tag_id: Tag ID

        Returns:
            Optional[Dict[str, Any]]: Tag data, or None if not found
        """
        async with self._db.execute(
            "SELECT id, name, description, created_at, modified_at FROM tags WHERE id = ?",
            (tag_id,),
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return dict(row)
            return None

    async def get_tag_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get a tag by name.

        Args:
            name: Tag name

        Returns:
            Optional[Dict[str, Any]]: Tag data, or None if not found
        """
        name = name.strip().lower()
        async with self._db.execute(
            "SELECT id, name, description, created_at, modified_at FROM tags WHERE name = ?",
            (name,),
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return dict(row)
            return None

    async def update_tag(
        self, tag_id: int, name: Optional[str] = None, description: Optional[str] = None
    ) -> bool:
        """
        Update a tag's name and/or description.

        Args:
            tag_id: Tag ID
            name: New tag name (optional)
            description: New tag description (optional)

        Returns:
            bool: True if the tag was updated, False if not found

        Raises:
            sqlite3.IntegrityError: If the new name conflicts with an existing tag
        """
        # Get current tag data
        tag = await self.get_tag(tag_id)
        if not tag:
            return False

        # Prepare update values
        update_name = name.strip().lower() if name else tag["name"]
        update_description = (
            description if description is not None else tag["description"]
        )

        # Skip if no changes
        if update_name == tag["name"] and update_description == tag["description"]:
            return True

        # Update the tag
        try:
            async with self._db.execute(
                "UPDATE tags SET name = ?, description = ? WHERE id = ?",
                (update_name, update_description, tag_id),
            ) as cursor:
                await self._db.commit()
                updated = cursor.rowcount > 0
                if updated:
                    logger.debug(f"Updated tag {tag_id}: {update_name}")
                return updated
        except sqlite3.IntegrityError:
            logger.warning(
                f"Cannot update tag {tag_id} to '{update_name}': name already exists"
            )
            raise

    async def delete_tag(self, tag_id: int) -> bool:
        """
        Delete a tag and all its associations.

        Args:
            tag_id: Tag ID

        Returns:
            bool: True if the tag was deleted, False if not found
        """
        async with self._db.execute(
            "DELETE FROM tags WHERE id = ?", (tag_id,)
        ) as cursor:
            await self._db.commit()
            deleted = cursor.rowcount > 0
            if deleted:
                logger.debug(f"Deleted tag {tag_id}")
            return deleted

    async def get_all_tags(self) -> List[Dict[str, Any]]:
        """
        Get all tags.

        Returns:
            List[Dict[str, Any]]: List of all tags
        """
        async with self._db.execute(
            "SELECT id, name, description, created_at, modified_at FROM tags ORDER BY name"
        ) as cursor:
            return [dict(row) for row in await cursor.fetchall()]

    # File tag operations

    async def add_file_tag(
        self,
        file_path: Path,
        tag_id: Optional[int] = None,
        tag_name: Optional[str] = None,
        source: str = "manual",
        confidence: float = 1.0,
    ) -> bool:
        """
        Add a tag to a file.

        Either tag_id or tag_name must be provided.

        Args:
            file_path: Path to the file
            tag_id: Tag ID (optional)
            tag_name: Tag name (optional)
            source: Source of the tag ('manual', 'auto', 'suggested')
            confidence: Confidence score for the tag (0.0-1.0)

        Returns:
            bool: True if the tag was added, False if already exists

        Raises:
            ValueError: If neither tag_id nor tag_name is provided, or if the tag doesn't exist
        """
        if tag_id is None and tag_name is None:
            raise ValueError("Either tag_id or tag_name must be provided")

        # If tag_name is provided, get or create the tag
        if tag_id is None:
            tag = await self.get_tag_by_name(tag_name)
            if not tag:
                tag_id = await self.create_tag(tag_name)
            else:
                tag_id = tag["id"]

        # Normalize file path
        file_path_str = str(file_path.resolve())

        # Add the file tag
        try:
            async with self._db.execute(
                "INSERT INTO file_tags (file_path, tag_id, source, confidence) VALUES (?, ?, ?, ?)",
                (file_path_str, tag_id, source, confidence),
            ):
                await self._db.commit()
                logger.debug(f"Added tag {tag_id} to file '{file_path}'")
                return True
        except sqlite3.IntegrityError:
            # Update the existing tag if it already exists
            async with self._db.execute(
                "UPDATE file_tags SET source = ?, confidence = ? WHERE file_path = ? AND tag_id = ?",
                (source, confidence, file_path_str, tag_id),
            ):
                await self._db.commit()
                logger.debug(f"Updated tag {tag_id} for file '{file_path}'")
                return False

    async def add_file_tags(
        self, file_path: Path, tags: List[Tuple[str, float]], source: str = "auto"
    ) -> int:
        """
        Add multiple tags to a file.

        Args:
            file_path: Path to the file
            tags: List of (tag_name, confidence) tuples
            source: Source of the tags

        Returns:
            int: Number of tags added
        """
        count = 0
        for tag_name, confidence in tags:
            try:
                added = await self.add_file_tag(
                    file_path=file_path,
                    tag_name=tag_name,
                    source=source,
                    confidence=confidence,
                )
                if added:
                    count += 1
            except Exception as e:
                logger.error(f"Error adding tag '{tag_name}' to '{file_path}': {e}")
        return count

    async def remove_file_tag(self, file_path: Path, tag_id: int) -> bool:
        """
        Remove a tag from a file.

        Args:
            file_path: Path to the file
            tag_id: Tag ID

        Returns:
            bool: True if the tag was removed, False if not found
        """
        file_path_str = str(file_path.resolve())
        async with self._db.execute(
            "DELETE FROM file_tags WHERE file_path = ? AND tag_id = ?",
            (file_path_str, tag_id),
        ) as cursor:
            await self._db.commit()
            removed = cursor.rowcount > 0
            if removed:
                logger.debug(f"Removed tag {tag_id} from file '{file_path}'")
            return removed

    async def remove_file_tags(
        self, file_path: Path, source: Optional[str] = None
    ) -> int:
        """
        Remove all tags from a file, optionally filtering by source.

        Args:
            file_path: Path to the file
            source: Optional source filter

        Returns:
            int: Number of tags removed
        """
        file_path_str = str(file_path.resolve())
        if source:
            async with self._db.execute(
                "DELETE FROM file_tags WHERE file_path = ? AND source = ?",
                (file_path_str, source),
            ) as cursor:
                await self._db.commit()
                count = cursor.rowcount
        else:
            async with self._db.execute(
                "DELETE FROM file_tags WHERE file_path = ?", (file_path_str,)
            ) as cursor:
                await self._db.commit()
                count = cursor.rowcount

        if count > 0:
            logger.debug(f"Removed {count} tags from file '{file_path}'")
        return count

    async def get_file_tags(
        self, file_path: Path, min_confidence: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Get all tags for a file.

        Args:
            file_path: Path to the file
            min_confidence: Minimum confidence threshold

        Returns:
            List[Dict[str, Any]]: List of tags with metadata
        """
        file_path_str = str(file_path.resolve())
        async with self._db.execute(
            """
            SELECT t.id, t.name, t.description, ft.source, ft.confidence, ft.added_at
            FROM file_tags ft
            JOIN tags t ON ft.tag_id = t.id
            WHERE ft.file_path = ? AND ft.confidence >= ?
            ORDER BY ft.confidence DESC, t.name
            """,
            (file_path_str, min_confidence),
        ) as cursor:
            return [dict(row) for row in await cursor.fetchall()]

    # Query operations

    async def get_files_by_tag(
        self,
        tag_id: Optional[int] = None,
        tag_name: Optional[str] = None,
        min_confidence: float = 0.0,
    ) -> List[str]:
        """
        Get all files with a specific tag.

        Either tag_id or tag_name must be provided.

        Args:
            tag_id: Tag ID (optional)
            tag_name: Tag name (optional)
            min_confidence: Minimum confidence threshold

        Returns:
            List[str]: List of file paths

        Raises:
            ValueError: If neither tag_id nor tag_name is provided
        """
        if tag_id is None and tag_name is None:
            raise ValueError("Either tag_id or tag_name must be provided")

        if tag_id is None:
            tag = await self.get_tag_by_name(tag_name)
            if not tag:
                return []
            tag_id = tag["id"]

        async with self._db.execute(
            """
            SELECT file_path FROM file_tags
            WHERE tag_id = ? AND confidence >= ?
            ORDER BY file_path
            """,
            (tag_id, min_confidence),
        ) as cursor:
            return [row[0] for row in await cursor.fetchall()]

    async def get_files_by_tags(
        self, tag_ids: List[int], require_all: bool = False, min_confidence: float = 0.0
    ) -> List[str]:
        """
        Get files that have specified tags.

        Args:
            tag_ids: List of tag IDs
            require_all: If True, files must have all tags; if False, any tag
            min_confidence: Minimum confidence threshold

        Returns:
            List[str]: List of file paths
        """
        if not tag_ids:
            return []

        if require_all:
            # Files must have ALL the specified tags
            placeholders = ",".join("?" for _ in tag_ids)
            async with self._db.execute(
                f"""
                SELECT file_path FROM file_tags
                WHERE tag_id IN ({placeholders}) AND confidence >= ?
                GROUP BY file_path
                HAVING COUNT(DISTINCT tag_id) = ?
                ORDER BY file_path
                """,
                (*tag_ids, min_confidence, len(tag_ids)),
            ) as cursor:
                return [row[0] for row in await cursor.fetchall()]
        else:
            # Files can have ANY of the specified tags
            placeholders = ",".join("?" for _ in tag_ids)
            async with self._db.execute(
                f"""
                SELECT DISTINCT file_path FROM file_tags
                WHERE tag_id IN ({placeholders}) AND confidence >= ?
                ORDER BY file_path
                """,
                (*tag_ids, min_confidence),
            ) as cursor:
                return [row[0] for row in await cursor.fetchall()]

    # Statistics and analytics

    async def get_tag_counts(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get tags with their usage counts.

        Args:
            limit: Maximum number of tags to return

        Returns:
            List[Dict[str, Any]]: List of tags with count information
        """
        async with self._db.execute(
            """
            SELECT t.id, t.name, t.description, COUNT(ft.file_path) as count
            FROM tags t
            LEFT JOIN file_tags ft ON t.id = ft.tag_id
            GROUP BY t.id
            ORDER BY count DESC, t.name
            LIMIT ?
            """,
            (limit,),
        ) as cursor:
            return [dict(row) for row in await cursor.fetchall()]

    async def get_tag_suggestions(
        self, file_path: Path, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get tag suggestions for a file based on similar files.

        This implements a simple collaborative filtering approach by
        suggesting tags that are commonly used with the file's existing tags.

        Args:
            file_path: Path to the file
            limit: Maximum number of suggestions to return

        Returns:
            List[Dict[str, Any]]: List of suggested tags with scores
        """
        file_path_str = str(file_path.resolve())

        # Get current tags
        current_tags = await self.get_file_tags(file_path)
        current_tag_ids = [tag["id"] for tag in current_tags]

        if not current_tag_ids:
            # No existing tags, return popular tags
            return await self.get_tag_counts(limit=limit)

        # Find other files with these tags
        placeholders = ",".join("?" for _ in current_tag_ids)
        async with self._db.execute(
            f"""
            SELECT DISTINCT file_path FROM file_tags
            WHERE tag_id IN ({placeholders}) AND file_path != ?
            """,
            (*current_tag_ids, file_path_str),
        ) as cursor:
            similar_files = [row[0] for row in await cursor.fetchall()]

        if not similar_files:
            return []

        # Find tags used in these files that aren't already on our file
        placeholders = ",".join("?" for _ in similar_files)
        async with self._db.execute(
            f"""
            SELECT t.id, t.name, t.description, COUNT(DISTINCT ft.file_path) as count
            FROM file_tags ft
            JOIN tags t ON ft.tag_id = t.id
            WHERE ft.file_path IN ({placeholders})
            AND t.id NOT IN ({','.join('?' for _ in current_tag_ids)})
            GROUP BY t.id
            ORDER BY count DESC, t.name
            LIMIT ?
            """,
            (*similar_files, *current_tag_ids, limit),
        ) as cursor:
            suggestions = []
            for row in await cursor.fetchall():
                data = dict(row)
                # Calculate score based on co-occurrence frequency
                data["score"] = data["count"] / len(similar_files)
                suggestions.append(data)
            return suggestions

    # Batch operations

    async def batch_add_tags(self, tag_data: List[Dict[str, Any]]) -> int:
        """
        Add multiple tags in a batch operation.

        Args:
            tag_data: List of dicts with 'name' and optional 'description'

        Returns:
            int: Number of tags added
        """
        count = 0
        async with self._db.executemany(
            "INSERT OR IGNORE INTO tags (name, description) VALUES (?, ?)",
            [(d["name"].strip().lower(), d.get("description")) for d in tag_data],
        ):
            await self._db.commit()
            count = self._db.total_changes

        logger.debug(f"Added {count} tags in batch")
        return count

    async def batch_add_file_tags(self, file_tags: List[Dict[str, Any]]) -> int:
        """
        Add multiple file tags in a batch operation.

        Args:
            file_tags: List of dicts with 'file_path', 'tag_name', optional 'source' and 'confidence'

        Returns:
            int: Number of file tags added
        """
        # First, ensure all tags exist
        tag_names = {item["tag_name"].strip().lower() for item in file_tags}
        await self.batch_add_tags([{"name": name} for name in tag_names])

        # Get tag IDs by name
        tag_id_map = {}
        for tag_name in tag_names:
            tag = await self.get_tag_by_name(tag_name)
            if tag:
                tag_id_map[tag_name] = tag["id"]

        # Add file tags
        data = []
        for item in file_tags:
            tag_name = item["tag_name"].strip().lower()
            if tag_name in tag_id_map:
                file_path_str = str(Path(item["file_path"]).resolve())
                data.append(
                    (
                        file_path_str,
                        tag_id_map[tag_name],
                        item.get("source", "auto"),
                        item.get("confidence", 1.0),
                    )
                )

        count = 0
        if data:
            try:
                async with self._db.executemany(
                    """
                    INSERT INTO file_tags (file_path, tag_id, source, confidence)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(file_path, tag_id) DO UPDATE SET
                    source = excluded.source,
                    confidence = excluded.confidence
                    """,
                    data,
                ):
                    await self._db.commit()
                    count = len(data)
            except Exception as e:
                logger.error(f"Error in batch_add_file_tags: {e}")

        logger.debug(f"Added {count} file tags in batch")
        return count

    # Cleanup and maintenance

    async def remove_orphaned_tags(self) -> int:
        """
        Remove tags that are not associated with any files.

        Returns:
            int: Number of tags removed
        """
        async with self._db.execute(
            """
            DELETE FROM tags
            WHERE id NOT IN (SELECT DISTINCT tag_id FROM file_tags)
            """
        ) as cursor:
            await self._db.commit()
            count = cursor.rowcount

        if count > 0:
            logger.debug(f"Removed {count} orphaned tags")
        return count

    async def remove_missing_file_tags(self) -> int:
        """
        Remove tags for files that no longer exist.

        Returns:
            int: Number of file tags removed
        """
        # This requires checking file existence for each path, which may be expensive
        # A more efficient approach would be to pass in a list of known valid paths

        # Get all file paths
        async with self._db.execute(
            "SELECT DISTINCT file_path FROM file_tags"
        ) as cursor:
            file_paths = [row[0] for row in await cursor.fetchall()]

        # Find paths that don't exist
        missing_paths = [path for path in file_paths if not Path(path).exists()]

        # Remove tags for missing files
        count = 0
        if missing_paths:
            placeholders = ",".join("?" for _ in missing_paths)
            async with self._db.execute(
                f"DELETE FROM file_tags WHERE file_path IN ({placeholders})",
                missing_paths,
            ) as cursor:
                await self._db.commit()
                count = cursor.rowcount

        if count > 0:
            logger.debug(f"Removed {count} tags for {len(missing_paths)} missing files")
        return count
