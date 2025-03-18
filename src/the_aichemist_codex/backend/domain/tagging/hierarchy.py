"""
Tag hierarchy management for organizing tags in a hierarchical structure.

This module provides the TagHierarchy class, which manages parent-child
relationships between tags, enabling more powerful organization and
categorization of files.
"""

import logging
import sqlite3
from typing import Any

logger = logging.getLogger(__name__)


class TagHierarchy:
    """
    Manages hierarchical relationships between tags.

    This class provides methods for creating, retrieving, and managing
    parent-child relationships between tags, enabling the organization
    of tags into a hierarchical structure.
    """

    def __init__(self, conn: sqlite3.Connection):
        """
        Initialize the tag hierarchy with a database connection.

        Args:
            conn: SQLite database connection
        """
        self.conn = conn

    def add_relationship(self, parent_id: int, child_id: int) -> bool:
        """
        Add a parent-child relationship between two tags.

        Args:
            parent_id: ID of the parent tag
            child_id: ID of the child tag

        Returns:
            bool: True if the relationship was added, False if it already exists
                 or would create a cycle

        Raises:
            sqlite3.IntegrityError: If the parent or child tag doesn't exist
        """
        # Check for potential cycles
        if self._would_create_cycle(parent_id, child_id):
            logger.warning(
                f"Cannot add relationship {parent_id} -> {child_id}: would create cycle"
            )
            return False

        try:
            cursor = self.conn.execute(
                "INSERT INTO tag_hierarchy (parent_id, child_id) VALUES (?, ?)",
                (parent_id, child_id),
            )
            self.conn.commit()
            added = cursor.rowcount > 0
            if added:
                logger.debug(
                    f"Added tag hierarchy relationship: {parent_id} -> {child_id}"
                )
            return added
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed" in str(e):
                logger.debug(f"Relationship already exists: {parent_id} -> {child_id}")
                return False
            logger.error(f"Error adding relationship {parent_id} -> {child_id}: {e}")
            raise

    def remove_relationship(self, parent_id: int, child_id: int) -> bool:
        """
        Remove a parent-child relationship between two tags.

        Args:
            parent_id: ID of the parent tag
            child_id: ID of the child tag

        Returns:
            bool: True if the relationship was removed, False if not found
        """
        cursor = self.conn.execute(
            "DELETE FROM tag_hierarchy WHERE parent_id = ? AND child_id = ?",
            (parent_id, child_id),
        )
        self.conn.commit()
        removed = cursor.rowcount > 0
        if removed:
            logger.debug(
                f"Removed tag hierarchy relationship: {parent_id} -> {child_id}"
            )
        return removed

    def get_parents(self, tag_id: int) -> list[dict[str, Any]]:
        """
        Get direct parent tags of a tag.

        Args:
            tag_id: ID of the tag

        Returns:
            List of dictionaries containing parent tag information
        """
        cursor = self.conn.execute(
            """
            SELECT t.*
            FROM tag_hierarchy h
            JOIN tags t ON h.parent_id = t.id
            WHERE h.child_id = ?
            ORDER BY t.name
            """,
            (tag_id,),
        )
        return [
            {
                "id": row[0],
                "name": row[1],
                "description": row[2],
                "created_at": row[3],
                "modified_at": row[4],
            }
            for row in cursor.fetchall()
        ]

    def get_children(self, tag_id: int) -> list[dict[str, Any]]:
        """
        Get direct child tags of a tag.

        Args:
            tag_id: ID of the tag

        Returns:
            List of dictionaries containing child tag information
        """
        cursor = self.conn.execute(
            """
            SELECT t.*
            FROM tag_hierarchy h
            JOIN tags t ON h.child_id = t.id
            WHERE h.parent_id = ?
            ORDER BY t.name
            """,
            (tag_id,),
        )
        return [
            {
                "id": row[0],
                "name": row[1],
                "description": row[2],
                "created_at": row[3],
                "modified_at": row[4],
            }
            for row in cursor.fetchall()
        ]

    def get_ancestors(self, tag_id: int) -> list[dict[str, Any]]:
        """
        Get all ancestor tags of a tag (recursively).

        Args:
            tag_id: ID of the tag

        Returns:
            List of dictionaries containing ancestor tag information
        """
        # Using recursive CTE to get all ancestors
        cursor = self.conn.execute(
            """
            WITH RECURSIVE ancestors(id) AS (
                SELECT parent_id FROM tag_hierarchy WHERE child_id = ?
                UNION
                SELECT h.parent_id FROM tag_hierarchy h
                JOIN ancestors a ON h.child_id = a.id
            )
            SELECT t.* FROM tags t
            JOIN ancestors a ON t.id = a.id
            ORDER BY t.name
            """,
            (tag_id,),
        )
        return [
            {
                "id": row[0],
                "name": row[1],
                "description": row[2],
                "created_at": row[3],
                "modified_at": row[4],
            }
            for row in cursor.fetchall()
        ]

    def get_descendants(self, tag_id: int) -> list[dict[str, Any]]:
        """
        Get all descendant tags of a tag (recursively).

        Args:
            tag_id: ID of the tag

        Returns:
            List of dictionaries containing descendant tag information
        """
        # Using recursive CTE to get all descendants
        cursor = self.conn.execute(
            """
            WITH RECURSIVE descendants(id) AS (
                SELECT child_id FROM tag_hierarchy WHERE parent_id = ?
                UNION
                SELECT h.child_id FROM tag_hierarchy h
                JOIN descendants d ON h.parent_id = d.id
            )
            SELECT t.* FROM tags t
            JOIN descendants d ON t.id = d.id
            ORDER BY t.name
            """,
            (tag_id,),
        )
        return [
            {
                "id": row[0],
                "name": row[1],
                "description": row[2],
                "created_at": row[3],
                "modified_at": row[4],
            }
            for row in cursor.fetchall()
        ]

    def _would_create_cycle(self, parent_id: int, child_id: int) -> bool:
        """
        Check if adding a relationship would create a cycle.

        A cycle would be created if:
        1. parent_id equals child_id
        2. child_id is already an ancestor of parent_id

        Args:
            parent_id: ID of the parent tag
            child_id: ID of the child tag

        Returns:
            bool: True if adding the relationship would create a cycle
        """
        # Check if parent and child are the same
        if parent_id == child_id:
            return True

        # Check if child is already an ancestor of parent
        # Using recursive CTE to get all ancestors of parent
        cursor = self.conn.execute(
            """
            WITH RECURSIVE ancestors(id) AS (
                SELECT parent_id FROM tag_hierarchy WHERE child_id = ?
                UNION
                SELECT h.parent_id FROM tag_hierarchy h
                JOIN ancestors a ON h.child_id = a.id
            )
            SELECT 1 FROM ancestors WHERE id = ?
            """,
            (parent_id, child_id),
        )
        return cursor.fetchone() is not None
