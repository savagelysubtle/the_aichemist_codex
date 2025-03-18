"""
Tagging manager for file organization.

This module provides the TaggingManagerImpl class, which is responsible for
managing file tags, including creating, retrieving, updating, and
deleting tags and their associations with files.
"""

import logging
import os
import sqlite3
from pathlib import Path
from typing import Any, cast

from ...core.exceptions import FileError, TagError, UnsafePathError
from ...core.interfaces import TaggingManager as TaggingManagerInterface
from ...registry import Registry
from .schema import TagSchema

logger = logging.getLogger(__name__)


class TaggingManagerImpl(TaggingManagerInterface):
    """
    Implementation of the TaggingManager interface.

    This class provides methods for creating, retrieving, updating, and
    deleting tags and their associations with files. It also provides
    methods for querying files by tags and retrieving tag statistics.
    """

    def __init__(self):
        """Initialize the TaggingManagerImpl."""
        self._registry = Registry.get_instance()
        self._validator = self._registry.file_validator
        self._paths = self._registry.project_paths

        # Get the path to the tag database file
        self._db_path = self._paths.get_data_dir() / "tags.db"
        self._schema = TagSchema(self._db_path)

    async def initialize(self) -> None:
        """
        Initialize the tag manager and create database tables if needed.

        Raises:
            Exception: If initialization fails
        """
        await self._schema.initialize()
        logger.info("Initialized TaggingManager")

    async def close(self) -> None:
        """Close any resources used by the tag manager."""
        logger.debug("Closed TaggingManager")

    async def create_tag(self, name: str, description: str = "") -> int:
        """
        Create a new tag.

        Args:
            name: Name of the tag (must be unique)
            description: Optional description of the tag

        Returns:
            The ID of the newly created tag

        Raises:
            TagError: If tag creation fails or a tag with the same name already exists
        """
        try:
            name = name.strip()
            if not name:
                raise TagError("Tag name cannot be empty")

            conn = await self._schema.get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO tags (name, description) VALUES (?, ?)",
                    (name, description),
                )
                conn.commit()
                tag_id = cursor.lastrowid
                if tag_id is None:
                    raise TagError(f"Failed to create tag: {name}")
                return cast(int, tag_id)
            except sqlite3.IntegrityError:
                raise TagError(f"Tag with name '{name}' already exists", tag_name=name)
            finally:
                conn.close()
        except Exception as e:
            if not isinstance(e, TagError):
                logger.error(f"Error creating tag: {e}")
                raise TagError(f"Failed to create tag: {e}", tag_name=name)
            raise

    async def get_tag(self, tag_id: int) -> dict[str, Any] | None:
        """
        Get tag information by ID.

        Args:
            tag_id: ID of the tag to retrieve

        Returns:
            Tag information as a dictionary, or None if not found
        """
        try:
            conn = await self._schema.get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, name, description, created_at, modified_at FROM tags WHERE id = ?",
                    (tag_id,),
                )
                row = cursor.fetchone()
                if row:
                    return dict(row)
                return None
            finally:
                conn.close()
        except Exception as e:
            logger.error(f"Error getting tag: {e}")
            raise TagError(f"Failed to get tag: {e}", tag_id=tag_id)

    async def get_tag_by_name(self, name: str) -> dict[str, Any] | None:
        """
        Get tag information by name.

        Args:
            name: Name of the tag to retrieve

        Returns:
            Tag information as a dictionary, or None if not found
        """
        try:
            name = name.strip()
            conn = await self._schema.get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, name, description, created_at, modified_at FROM tags WHERE name = ?",
                    (name,),
                )
                row = cursor.fetchone()
                if row:
                    return dict(row)
                return None
            finally:
                conn.close()
        except Exception as e:
            logger.error(f"Error getting tag by name: {e}")
            raise TagError(f"Failed to get tag by name: {e}", tag_name=name)

    async def update_tag(
        self, tag_id: int, name: str | None = None, description: str | None = None
    ) -> bool:
        """
        Update an existing tag.

        Args:
            tag_id: ID of the tag to update
            name: New name for the tag (optional)
            description: New description for the tag (optional)

        Returns:
            True if the tag was updated, False otherwise

        Raises:
            TagError: If the tag does not exist or the update fails
        """
        if name is None and description is None:
            return False

        try:
            # Get the tag to make sure it exists
            tag = await self.get_tag(tag_id)
            if not tag:
                raise TagError(f"Tag with ID {tag_id} does not exist", tag_id=tag_id)

            # Prepare update values
            updates = []
            params = []

            if name is not None:
                name = name.strip()
                if not name:
                    raise TagError("Tag name cannot be empty")
                updates.append("name = ?")
                params.append(name)

            if description is not None:
                updates.append("description = ?")
                params.append(description)

            updates.append("modified_at = CURRENT_TIMESTAMP")

            # Add tag_id to params
            params.append(tag_id)

            # Execute update
            conn = await self._schema.get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(
                    f"UPDATE tags SET {', '.join(updates)} WHERE id = ?", tuple(params)
                )
                conn.commit()
                return cursor.rowcount > 0
            except sqlite3.IntegrityError:
                raise TagError(f"Tag with name '{name}' already exists", tag_name=name)
            finally:
                conn.close()
        except Exception as e:
            if not isinstance(e, TagError):
                logger.error(f"Error updating tag: {e}")
                raise TagError(f"Failed to update tag: {e}", tag_id=tag_id)
            raise

    async def delete_tag(self, tag_id: int) -> bool:
        """
        Delete a tag.

        Args:
            tag_id: ID of the tag to delete

        Returns:
            True if the tag was deleted, False otherwise

        Raises:
            TagError: If the tag does not exist or the deletion fails
        """
        try:
            # Get the tag to make sure it exists
            tag = await self.get_tag(tag_id)
            if not tag:
                raise TagError(f"Tag with ID {tag_id} does not exist", tag_id=tag_id)

            conn = await self._schema.get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM tags WHERE id = ?", (tag_id,))
                conn.commit()
                return cursor.rowcount > 0
            finally:
                conn.close()
        except Exception as e:
            if not isinstance(e, TagError):
                logger.error(f"Error deleting tag: {e}")
                raise TagError(f"Failed to delete tag: {e}", tag_id=tag_id)
            raise

    async def get_all_tags(self) -> list[dict[str, Any]]:
        """
        Get all tags.

        Returns:
            A list of dictionaries containing tag information
        """
        try:
            conn = await self._schema.get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, name, description, created_at, modified_at FROM tags ORDER BY name"
                )
                tags = [dict(row) for row in cursor.fetchall()]
                return tags
            finally:
                conn.close()
        except Exception as e:
            logger.error(f"Error getting all tags: {e}")
            raise TagError(f"Failed to get all tags: {e}")

    async def add_file_tag(
        self,
        file_path: Path,
        tag_id: int | None = None,
        tag_name: str | None = None,
        source: str = "manual",
        confidence: float = 1.0,
    ) -> bool:
        """
        Add a tag to a file.

        Args:
            file_path: Path to the file
            tag_id: ID of the tag to add (either tag_id or tag_name must be provided)
            tag_name: Name of the tag to add (either tag_id or tag_name must be provided)
            source: Source of the tag (e.g., "manual", "auto", "suggested")
            confidence: Confidence score for the tag (0.0 to 1.0)

        Returns:
            True if the tag was added, False otherwise

        Raises:
            TagError: If neither tag_id nor tag_name is provided, or if the tag does not exist
            FileError: If the file does not exist
        """
        try:
            # Ensure file exists and path is safe
            file_path = Path(str(file_path))
            file_path_str = str(file_path)
            self._validator.ensure_path_safe(file_path_str)

            if not os.path.exists(file_path):
                raise FileError(
                    f"File does not exist: {file_path}", file_path=file_path_str
                )

            # Get or create tag
            if tag_id is None and tag_name is None:
                raise TagError("Either tag_id or tag_name must be provided")

            if tag_id is None:
                # Try to get tag by name
                assert tag_name is not None
                tag = await self.get_tag_by_name(tag_name)
                if tag is None:
                    # Create new tag
                    tag_id = await self.create_tag(tag_name)
                else:
                    tag_id = tag["id"]

            # Clamp confidence to [0, 1]
            confidence = max(0.0, min(1.0, confidence))

            # Add tag to file
            conn = await self._schema.get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO file_tags (file_path, tag_id, source, confidence)
                    VALUES (?, ?, ?, ?)
                    """,
                    (file_path_str, tag_id, source, confidence),
                )
                conn.commit()
                return cursor.rowcount > 0
            finally:
                conn.close()
        except Exception as e:
            if isinstance(e, (FileError, TagError)):
                raise
            logger.error(f"Error adding file tag: {e}")
            raise TagError(
                f"Failed to add file tag: {e}", tag_id=tag_id, tag_name=tag_name
            )

    async def add_file_tags(
        self, file_path: Path, tags: list[tuple[str, float]], source: str = "auto"
    ) -> int:
        """
        Add multiple tags to a file.

        Args:
            file_path: Path to the file
            tags: List of (tag_name, confidence) tuples
            source: Source of the tags (e.g., "manual", "auto", "suggested")

        Returns:
            Number of tags added

        Raises:
            FileError: If the file does not exist
        """
        try:
            # Ensure file exists and path is safe
            file_path = Path(str(file_path))
            file_path_str = str(file_path)
            self._validator.ensure_path_safe(file_path_str)

            if not os.path.exists(file_path):
                raise FileError(
                    f"File does not exist: {file_path}", file_path=file_path_str
                )

            count = 0
            for tag_name, confidence in tags:
                try:
                    if await self.add_file_tag(
                        file_path,
                        tag_name=tag_name,
                        confidence=confidence,
                        source=source,
                    ):
                        count += 1
                except Exception as e:
                    logger.warning(
                        f"Failed to add tag '{tag_name}' to file {file_path}: {e}"
                    )

            return count
        except Exception as e:
            if isinstance(e, FileError):
                raise
            logger.error(f"Error adding file tags: {e}")
            raise TagError(f"Failed to add file tags: {e}")

    async def remove_file_tag(self, file_path: Path, tag_id: int) -> bool:
        """
        Remove a tag from a file.

        Args:
            file_path: Path to the file
            tag_id: ID of the tag to remove

        Returns:
            True if the tag was removed, False otherwise

        Raises:
            TagError: If the tag does not exist
            FileError: If the file does not exist
        """
        try:
            # Ensure file exists and path is safe
            file_path = Path(str(file_path))
            file_path_str = str(file_path)
            self._validator.ensure_path_safe(file_path_str)

            if not os.path.exists(file_path):
                raise FileError(
                    f"File does not exist: {file_path}", file_path=file_path_str
                )

            # Check if tag exists
            tag = await self.get_tag(tag_id)
            if not tag:
                raise TagError(f"Tag with ID {tag_id} does not exist", tag_id=tag_id)

            # Remove tag from file
            conn = await self._schema.get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM file_tags WHERE file_path = ? AND tag_id = ?",
                    (file_path_str, tag_id),
                )
                conn.commit()
                return cursor.rowcount > 0
            finally:
                conn.close()
        except Exception as e:
            if isinstance(e, (FileError, TagError)):
                raise
            logger.error(f"Error removing file tag: {e}")
            raise TagError(f"Failed to remove file tag: {e}", tag_id=tag_id)

    async def get_file_tags(self, file_path: Path) -> list[dict[str, Any]]:
        """
        Get all tags for a file.

        Args:
            file_path: Path to the file

        Returns:
            List of dictionaries containing tag information
        """
        try:
            # Ensure path is safe
            file_path = Path(str(file_path))
            file_path_str = str(file_path)
            self._validator.ensure_path_safe(file_path_str)

            conn = await self._schema.get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT t.id, t.name, t.description,
                           ft.source, ft.confidence, ft.added_at
                    FROM file_tags ft
                    JOIN tags t ON ft.tag_id = t.id
                    WHERE ft.file_path = ?
                    ORDER BY t.name
                    """,
                    (file_path_str,),
                )
                tags = [dict(row) for row in cursor.fetchall()]
                return tags
            finally:
                conn.close()
        except Exception as e:
            if isinstance(e, UnsafePathError):
                raise
            logger.error(f"Error getting file tags: {e}")
            raise TagError(f"Failed to get file tags: {e}")

    async def get_files_by_tag(
        self, tag_id: int | None = None, tag_name: str | None = None
    ) -> list[str]:
        """
        Get all files with a specific tag.

        Args:
            tag_id: ID of the tag (either tag_id or tag_name must be provided)
            tag_name: Name of the tag (either tag_id or tag_name must be provided)

        Returns:
            List of file paths

        Raises:
            TagError: If neither tag_id nor tag_name is provided, or if the tag does not exist
        """
        try:
            if tag_id is None and tag_name is None:
                raise TagError("Either tag_id or tag_name must be provided")

            if tag_id is None:
                # Try to get tag by name
                assert tag_name is not None
                tag = await self.get_tag_by_name(tag_name)
                if tag is None:
                    raise TagError(
                        f"Tag with name '{tag_name}' does not exist", tag_name=tag_name
                    )
                tag_id = tag["id"]
            else:
                # Check if tag exists
                tag = await self.get_tag(tag_id)
                if not tag:
                    raise TagError(
                        f"Tag with ID {tag_id} does not exist", tag_id=tag_id
                    )

            conn = await self._schema.get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT file_path FROM file_tags WHERE tag_id = ? ORDER BY file_path",
                    (tag_id,),
                )
                files = [row["file_path"] for row in cursor.fetchall()]
                return files
            finally:
                conn.close()
        except Exception as e:
            if isinstance(e, TagError):
                raise
            logger.error(f"Error getting files by tag: {e}")
            raise TagError(
                f"Failed to get files by tag: {e}", tag_id=tag_id, tag_name=tag_name
            )

    async def get_files_by_tags(
        self, tag_ids: list[int], require_all: bool = False
    ) -> list[str]:
        """
        Get all files with specific tags.

        Args:
            tag_ids: List of tag IDs
            require_all: If True, files must have all tags; if False, files must have any of the tags

        Returns:
            List of file paths
        """
        try:
            if not tag_ids:
                return []

            # Verify all tags exist
            for tag_id in tag_ids:
                tag = await self.get_tag(tag_id)
                if not tag:
                    raise TagError(
                        f"Tag with ID {tag_id} does not exist", tag_id=tag_id
                    )

            conn = await self._schema.get_connection()
            try:
                cursor = conn.cursor()
                if require_all:
                    # Files must have all tags
                    query = """
                    SELECT file_path
                    FROM file_tags
                    WHERE tag_id IN ({})
                    GROUP BY file_path
                    HAVING COUNT(DISTINCT tag_id) = ?
                    ORDER BY file_path
                    """.format(",".join("?" * len(tag_ids)))
                    cursor.execute(query, tag_ids + [len(tag_ids)])
                else:
                    # Files must have any of the tags
                    query = """
                    SELECT DISTINCT file_path
                    FROM file_tags
                    WHERE tag_id IN ({})
                    ORDER BY file_path
                    """.format(",".join("?" * len(tag_ids)))
                    cursor.execute(query, tag_ids)

                files = [row["file_path"] for row in cursor.fetchall()]
                return files
            finally:
                conn.close()
        except Exception as e:
            if isinstance(e, TagError):
                raise
            logger.error(f"Error getting files by tags: {e}")
            raise TagError(f"Failed to get files by tags: {e}")

    async def get_tag_counts(self) -> list[dict[str, Any]]:
        """
        Get the number of files for each tag.

        Returns:
            List of dictionaries containing tag information and file counts
        """
        try:
            conn = await self._schema.get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT t.id, t.name, t.description, COUNT(ft.file_path) as file_count
                    FROM tags t
                    LEFT JOIN file_tags ft ON t.id = ft.tag_id
                    GROUP BY t.id
                    ORDER BY t.name
                    """
                )
                tag_counts = [dict(row) for row in cursor.fetchall()]
                return tag_counts
            finally:
                conn.close()
        except Exception as e:
            logger.error(f"Error getting tag counts: {e}")
            raise TagError(f"Failed to get tag counts: {e}")

    async def get_tag_suggestions(self, file_path: Path) -> list[dict[str, Any]]:
        """
        Get tag suggestions for a file.

        Args:
            file_path: Path to the file

        Returns:
            List of dictionaries containing suggested tag information and confidence scores
        """
        try:
            # Ensure path is safe
            file_path = Path(str(file_path))
            file_path_str = str(file_path)
            self._validator.ensure_path_safe(file_path_str)

            # Currently, we'll just return the most popular tags as suggestions
            # In a real implementation, this would use a more sophisticated algorithm
            conn = await self._schema.get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT t.id, t.name, t.description, COUNT(ft.file_path) as popularity
                    FROM tags t
                    JOIN file_tags ft ON t.id = ft.tag_id
                    WHERE ft.source = 'manual'
                    GROUP BY t.id
                    ORDER BY popularity DESC
                    LIMIT 10
                    """
                )
                suggestions = []
                for row in cursor.fetchall():
                    # Convert popularity to a confidence score (0.5 to 0.9)
                    popularity = row["popularity"]
                    confidence = min(0.9, 0.5 + (popularity / 20))

                    suggestion = {
                        "id": row["id"],
                        "name": row["name"],
                        "description": row["description"],
                        "confidence": confidence,
                    }
                    suggestions.append(suggestion)

                return suggestions
            finally:
                conn.close()
        except Exception as e:
            if isinstance(e, UnsafePathError):
                raise
            logger.error(f"Error getting tag suggestions: {e}")
            raise TagError(f"Failed to get tag suggestions: {e}")


# Export symbols
__all__ = ["TaggingManagerImpl"]
