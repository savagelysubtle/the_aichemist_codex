"""
Tag management system for file organization.

This module provides the TagManager class, which is responsible for
managing file tags, including creating, retrieving, updating, and
deleting tags and their associations with files.
"""

import logging
import sqlite3
from pathlib import Path
from typing import Any

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

    async def initialize(self) -> None:
        """
        Initialize the tag manager and create database tables if needed.

        Raises:
            Exception: If initialization fails
        """
        await self.schema.initialize()
        logger.info("Initialized TagManager")

    async def close(self) -> None:
        """Close any resources used by the tag manager."""
        logger.debug("Closed TagManager")

    async def __aenter__(self) -> "TagManager":
        """Support for async context manager."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Support for async context manager."""
        await self.close()

    # Tag operations

    async def create_tag(self, name: str, description: str = "") -> int:
        """
        Create a new tag.

        Args:
            name: Tag name
            description: Tag description

        Returns:
            int: Tag ID

        Raises:
            Exception: If tag creation fails
        """
        # Normalize tag name (lowercase, strip whitespace)
        name = name.strip().lower()

        # Insert tag and return ID
        try:
            # Check if tag already exists
            existing_tag = await self.get_tag_by_name(name)
            if existing_tag:
                return existing_tag["id"]

            # Create new tag
            query = "INSERT INTO tags (name, description) VALUES (?, ?)"
            await self.schema.db.execute(query, (name, description), commit=True)

            # Get the inserted tag ID
            result = await self.schema.db.fetchone(
                "SELECT id FROM tags WHERE name = ?", (name,)
            )
            if result:
                tag_id = result[0]
                logger.debug(f"Created tag: {name} (id: {tag_id})")
                return tag_id

            raise ValueError(f"Failed to retrieve ID for newly created tag: {name}")

        except Exception as e:
            logger.error(f"Error creating tag '{name}': {e}")
            raise

    async def get_tag(self, tag_id: int) -> dict[str, Any] | None:
        """
        Get a tag by ID.

        Args:
            tag_id: Tag ID

        Returns:
            Dict containing tag data, or None if not found
        """
        try:
            result = await self.schema.db.fetchone(
                "SELECT * FROM tags WHERE id = ?", (tag_id,)
            )
            if result:
                return {
                    "id": result[0],
                    "name": result[1],
                    "description": result[2],
                    "created_at": result[3],
                    "modified_at": result[4],
                }
            return None
        except Exception as e:
            logger.error(f"Error getting tag with id {tag_id}: {e}")
            return None

    async def get_tag_by_name(self, name: str) -> dict[str, Any] | None:
        """
        Get a tag by name (case insensitive).

        Args:
            name: Tag name

        Returns:
            Dict containing tag data, or None if not found
        """
        try:
            # Normalize tag name (lowercase, strip whitespace)
            name = name.strip().lower()

            result = await self.schema.db.fetchone(
                "SELECT * FROM tags WHERE LOWER(name) = ?", (name,)
            )
            if result:
                return {
                    "id": result[0],
                    "name": result[1],
                    "description": result[2],
                    "created_at": result[3],
                    "modified_at": result[4],
                }
            return None
        except Exception as e:
            logger.error(f"Error getting tag with name '{name}': {e}")
            return None

    async def update_tag(
        self, tag_id: int, name: str | None = None, description: str | None = None
    ) -> bool:
        """
        Update a tag.

        Args:
            tag_id: Tag ID
            name: New tag name (optional)
            description: New tag description (optional)

        Returns:
            bool: True if updated, False if not found or not updated
        """
        try:
            # Get current tag data
            tag = await self.get_tag(tag_id)
            if not tag:
                return False

            # Prepare update data
            update_data = []
            params = []
            if name is not None:
                # Normalize tag name (lowercase, strip whitespace)
                name = name.strip().lower()
                update_data.append("name = ?")
                params.append(name)
            if description is not None:
                update_data.append("description = ?")
                params.append(description)

            if not update_data:
                # Nothing to update
                return False

            # Build and execute update query
            query = f"UPDATE tags SET {', '.join(update_data)} WHERE id = ?"
            params.append(tag_id)
            await self.schema.db.execute(query, tuple(params), commit=True)
            logger.debug(f"Updated tag {tag_id}")
            return True

        except Exception as e:
            logger.error(f"Error updating tag {tag_id}: {e}")
            return False

    async def delete_tag(self, tag_id: int) -> bool:
        """
        Delete a tag.

        Args:
            tag_id: Tag ID

        Returns:
            bool: True if deleted, False if not found or not deleted
        """
        try:
            # Check if tag exists
            tag = await self.get_tag(tag_id)
            if not tag:
                return False

            # Delete tag (cascade will delete from tag_hierarchy and file_tags)
            await self.schema.db.execute(
                "DELETE FROM tags WHERE id = ?", (tag_id,), commit=True
            )
            logger.debug(f"Deleted tag {tag_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting tag {tag_id}: {e}")
            return False

    async def get_all_tags(self) -> list[dict[str, Any]]:
        """
        Get all tags.

        Returns:
            List of dicts containing tag data
        """
        try:
            results = await self.schema.db.fetchall("SELECT * FROM tags ORDER BY name")
            return [
                {
                    "id": row[0],
                    "name": row[1],
                    "description": row[2],
                    "created_at": row[3],
                    "modified_at": row[4],
                }
                for row in results
            ]
        except Exception as e:
            logger.error(f"Error getting all tags: {e}")
            return []

    # File tag operations

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

        Either tag_id or tag_name must be provided.

        Args:
            file_path: Path to the file
            tag_id: ID of the tag to add
            tag_name: Name of the tag to add (alternative to tag_id)
            source: Source of the tag (e.g., "manual", "auto")
            confidence: Confidence score (0.0 to 1.0)

        Returns:
            bool: True if a new tag was added, False if an existing tag was updated

        Raises:
            ValueError: If neither tag_id nor tag_name is provided
            Exception: If tag addition fails
        """
        if tag_id is None and tag_name is None:
            raise ValueError("Either tag_id or tag_name must be provided")

        file_path_str = str(file_path.resolve())

        # If tag_name is provided, get or create the tag
        if tag_id is None and tag_name is not None:
            tag = await self.get_tag_by_name(tag_name)
            if tag:
                tag_id = tag["id"]
            else:
                tag_id = await self.create_tag(tag_name)

        # At this point, tag_id should be set
        assert tag_id is not None, "tag_id should not be None at this point"

        # Try to insert the file tag
        try:
            # First try to insert
            await self.schema.db.execute(
                "INSERT INTO file_tags (file_path, tag_id, source, confidence) VALUES (?, ?, ?, ?)",
                (file_path_str, tag_id, source, confidence),
                commit=True,
            )
            logger.debug(f"Added tag {tag_id} to file '{file_path}'")
            return True
        except sqlite3.IntegrityError:
            # Update if already exists
            await self.schema.db.execute(
                "UPDATE file_tags SET source = ?, confidence = ? WHERE file_path = ? AND tag_id = ?",
                (source, confidence, file_path_str, tag_id),
                commit=True,
            )
            logger.debug(f"Updated tag {tag_id} for file '{file_path}'")
            return False
        except Exception as e:
            logger.error(f"Error adding tag {tag_id} to file '{file_path}': {e}")
            raise

    async def add_file_tags(
        self, file_path: Path, tags: list[tuple[str, float]], source: str = "auto"
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
        try:
            result = await self.schema.db.fetchone(
                "SELECT 1 FROM file_tags WHERE file_path = ? AND tag_id = ?",
                (file_path_str, tag_id),
            )
            if not result:
                return False

            await self.schema.db.execute(
                "DELETE FROM file_tags WHERE file_path = ? AND tag_id = ?",
                (file_path_str, tag_id),
                commit=True,
            )
            logger.debug(f"Removed tag {tag_id} from file '{file_path}'")
            return True
        except Exception as e:
            logger.error(f"Error removing tag {tag_id} from file '{file_path}': {e}")
            return False

    async def get_file_tags(self, file_path: Path) -> list[dict[str, Any]]:
        """
        Get all tags for a file.

        Args:
            file_path: Path to the file

        Returns:
            List of dicts containing tag data
        """
        file_path_str = str(file_path.resolve())
        try:
            results = await self.schema.db.fetchall(
                """
                SELECT t.id, t.name, t.description, ft.source, ft.confidence
                FROM file_tags ft
                JOIN tags t ON ft.tag_id = t.id
                WHERE ft.file_path = ?
                ORDER BY t.name
                """,
                (file_path_str,),
            )
            return [
                {
                    "id": row[0],
                    "name": row[1],
                    "description": row[2],
                    "source": row[3],
                    "confidence": row[4],
                }
                for row in results
            ]
        except Exception as e:
            logger.error(f"Error getting tags for file '{file_path}': {e}")
            return []

    # Query operations

    async def get_files_by_tag(
        self, tag_id: int | None = None, tag_name: str | None = None
    ) -> list[str]:
        """
        Get all files with a specific tag.

        Either tag_id or tag_name must be provided.

        Args:
            tag_id: Tag ID
            tag_name: Tag name

        Returns:
            List[str]: List of file paths

        Raises:
            ValueError: If neither tag_id nor tag_name is provided
        """
        if tag_id is None and tag_name is None:
            raise ValueError("Either tag_id or tag_name must be provided")

        # If tag_name is provided, get tag ID
        if tag_id is None and tag_name is not None:
            tag = await self.get_tag_by_name(tag_name)
            if not tag:
                return []
            tag_id = tag["id"]

        # At this point, tag_id should be set
        assert tag_id is not None, "tag_id should not be None at this point"

        try:
            results = await self.schema.db.fetchall(
                "SELECT file_path FROM file_tags WHERE tag_id = ?", (tag_id,)
            )
            return [row[0] for row in results]
        except Exception as e:
            logger.error(f"Error getting files for tag {tag_id}: {e}")
            return []

    async def get_files_by_tags(
        self, tag_ids: list[int], require_all: bool = False
    ) -> list[str]:
        """
        Get files that have the specified tags.

        Args:
            tag_ids: List of tag IDs
            require_all: If True, files must have ALL tags; if False, ANY tag

        Returns:
            List[str]: List of file paths
        """
        if not tag_ids:
            return []

        try:
            if require_all:
                # Files must have ALL the specified tags
                placeholders = ",".join("?" for _ in tag_ids)
                results = await self.schema.db.fetchall(
                    f"""
                    SELECT file_path FROM file_tags
                    WHERE tag_id IN ({placeholders})
                    GROUP BY file_path
                    HAVING COUNT(DISTINCT tag_id) = ?
                    """,
                    tuple(tag_ids) + (len(tag_ids),),
                )
            else:
                # Files can have ANY of the specified tags
                placeholders = ",".join("?" for _ in tag_ids)
                results = await self.schema.db.fetchall(
                    f"""
                    SELECT DISTINCT file_path FROM file_tags
                    WHERE tag_id IN ({placeholders})
                    """,
                    tuple(tag_ids),
                )

            return [row[0] for row in results]
        except Exception as e:
            logger.error(f"Error getting files by tags: {e}")
            return []

    async def get_tag_counts(self) -> list[dict[str, Any]]:
        """
        Get all tags with their usage counts.

        Returns:
            List[Dict[str, Any]]: List of tags with count information
        """
        try:
            results = await self.schema.db.fetchall(
                """
                SELECT t.id, t.name, t.description, COUNT(ft.file_path) as count
                FROM tags t
                LEFT JOIN file_tags ft ON t.id = ft.tag_id
                GROUP BY t.id
                ORDER BY count DESC, t.name
                """
            )

            return [
                {
                    "id": row[0],
                    "name": row[1],
                    "description": row[2],
                    "count": row[3],
                }
                for row in results
            ]
        except Exception as e:
            logger.error(f"Error getting tag counts: {e}")
            return []

    # Batch operations

    async def batch_add_tags(self, tag_data: list[dict[str, Any]]) -> int:
        """
        Add multiple tags in a batch operation.

        Args:
            tag_data: List of dicts with 'name' and optional 'description' keys

        Returns:
            int: Number of tags added
        """
        if not tag_data:
            return 0

        try:
            # Prepare data for batch insert
            tag_entries = [
                (d["name"].strip().lower(), d.get("description", "")) for d in tag_data
            ]

            # Execute batch insert
            await self.schema.db.executemany(
                "INSERT OR IGNORE INTO tags (name, description) VALUES (?, ?)",
                tag_entries,
            )

            # Since we can't directly get the count from executemany,
            # we'll count by checking which tags now exist
            added_count = 0
            for tag_info in tag_data:
                tag_name = tag_info["name"].strip().lower()
                tag = await self.get_tag_by_name(tag_name)
                if tag:
                    added_count += 1

            logger.debug(f"Added {added_count} tags in batch")
            return added_count
        except Exception as e:
            logger.error(f"Error in batch_add_tags: {e}")
            return 0

    async def batch_add_file_tags(self, file_tags: list[dict[str, Any]]) -> int:
        """
        Add multiple file-tag associations in a batch operation.

        Args:
            file_tags: List of dicts with keys:
                       - file_path: Path to the file
                       - tag_name: Tag name
                       - source: Source of the tag (optional)
                       - confidence: Confidence score (optional)

        Returns:
            int: Number of file tags added
        """
        if not file_tags:
            return 0

        # First, ensure all tags exist and get their IDs
        tag_names = set(item["tag_name"].strip().lower() for item in file_tags)
        tag_id_map = {}

        for tag_name in tag_names:
            tag = await self.get_tag_by_name(tag_name)
            if tag:
                tag_id_map[tag_name] = tag["id"]
            else:
                # Create tag if it doesn't exist
                tag_id = await self.create_tag(tag_name)
                tag_id_map[tag_name] = tag_id

        # Prepare data for batch insert
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
                # Execute batch insert using the INSERT OR REPLACE pattern
                query = """
                INSERT INTO file_tags (file_path, tag_id, source, confidence)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(file_path, tag_id) DO UPDATE SET
                source = excluded.source,
                confidence = excluded.confidence
                """

                await self.schema.db.executemany(query, data)
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
        try:
            # First, identify orphaned tags
            results = await self.schema.db.fetchall(
                """
                SELECT id FROM tags
                WHERE id NOT IN (SELECT DISTINCT tag_id FROM file_tags)
                """
            )

            orphaned_tag_ids = [row[0] for row in results]

            if not orphaned_tag_ids:
                return 0

            # Delete the orphaned tags
            for tag_id in orphaned_tag_ids:
                await self.delete_tag(tag_id)

            count = len(orphaned_tag_ids)
            logger.debug(f"Removed {count} orphaned tags")
            return count
        except Exception as e:
            logger.error(f"Error removing orphaned tags: {e}")
            return 0

    async def clean_missing_files(self) -> int:
        """
        Remove tags for files that no longer exist.

        Returns:
            int: Number of file tags removed
        """
        try:
            # Get all file paths
            results = await self.schema.db.fetchall(
                "SELECT DISTINCT file_path FROM file_tags"
            )

            all_paths = [row[0] for row in results]
            missing_paths = []

            # Check which files no longer exist
            for path_str in all_paths:
                if not Path(path_str).exists():
                    missing_paths.append(path_str)

            if not missing_paths:
                return 0

            # Delete tags for missing files
            count = 0
            for path_str in missing_paths:
                # Execute delete for each missing file
                await self.schema.db.execute(
                    "DELETE FROM file_tags WHERE file_path = ?",
                    (path_str,),
                    commit=True,
                )
                count += 1

            logger.debug(f"Removed tags for {count} missing files")
            return count
        except Exception as e:
            logger.error(f"Error cleaning missing files: {e}")
            return 0

    async def get_tag_suggestions(self, file_path: Path) -> list[dict[str, Any]]:
        """
        Get tag suggestions for a file based on similar files.

        This method implements a collaborative filtering approach by finding files
        with similar extensions or in the same directory and recommending their tags.

        Args:
            file_path: Path to the file

        Returns:
            List[Dict[str, Any]]: List of suggested tags with scores
        """
        file_path_str = str(file_path.resolve())
        suggestions = {}

        try:
            # Get file directory and extension
            path = Path(file_path_str)
            directory = str(path.parent)
            extension = path.suffix.lower()

            # Find tags used on files with the same extension
            if extension:
                ext_results = await self.schema.db.fetchall(
                    """
                    SELECT t.id, t.name, COUNT(*) as count
                    FROM file_tags ft
                    JOIN tags t ON ft.tag_id = t.id
                    WHERE ft.file_path LIKE ?
                    AND ft.file_path != ?
                    GROUP BY t.id
                    ORDER BY count DESC
                    LIMIT 20
                    """,
                    (f"%{extension}", file_path_str),
                )

                # Add to suggestions with weight based on frequency
                max_count = max([row[2] for row in ext_results]) if ext_results else 1
                for row in ext_results:
                    tag_id, tag_name, count = row
                    score = min(0.85, 0.5 + (count / max_count) * 0.35)
                    suggestions[tag_name] = {
                        "name": tag_name,
                        "score": score,
                        "reason": "extension",
                    }

            # Find tags used on files in the same directory
            dir_results = await self.schema.db.fetchall(
                """
                SELECT t.id, t.name, COUNT(*) as count
                FROM file_tags ft
                JOIN tags t ON ft.tag_id = t.id
                WHERE ft.file_path LIKE ?
                AND ft.file_path != ?
                GROUP BY t.id
                ORDER BY count DESC
                LIMIT 20
                """,
                (f"{directory}%", file_path_str),
            )

            # Add to suggestions with weight based on frequency
            max_count = max([row[2] for row in dir_results]) if dir_results else 1
            for row in dir_results:
                tag_id, tag_name, count = row
                score = min(0.8, 0.5 + (count / max_count) * 0.3)
                if tag_name in suggestions:
                    # Take the higher score if already suggested
                    if score > suggestions[tag_name]["score"]:
                        suggestions[tag_name]["score"] = score
                        suggestions[tag_name]["reason"] = "directory"
                else:
                    suggestions[tag_name] = {
                        "name": tag_name,
                        "score": score,
                        "reason": "directory",
                    }

            # Convert to list and sort by score
            result = list(suggestions.values())
            result.sort(key=lambda x: x["score"], reverse=True)

            return result

        except Exception as e:
            logger.error(f"Error getting tag suggestions for file '{file_path}': {e}")
            return []
