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
            tag_id: Tag ID

        Returns:
            List[Dict[str, Any]]: List of parent tag data
        """
        cursor = self.conn.execute(
            """
            SELECT t.id, t.name, t.description
            FROM tag_hierarchy th
            JOIN tags t ON th.parent_id = t.id
            WHERE th.child_id = ?
            ORDER BY t.name
            """,
            (tag_id,),
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_children(self, tag_id: int) -> list[dict[str, Any]]:
        """
        Get direct child tags of a tag.

        Args:
            tag_id: Tag ID

        Returns:
            List[Dict[str, Any]]: List of child tag data
        """
        cursor = self.conn.execute(
            """
            SELECT t.id, t.name, t.description
            FROM tag_hierarchy th
            JOIN tags t ON th.child_id = t.id
            WHERE th.parent_id = ?
            ORDER BY t.name
            """,
            (tag_id,),
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_ancestors(self, tag_id: int) -> list[dict[str, Any]]:
        """
        Get all ancestor tags of a tag (recursive parents).

        Args:
            tag_id: Tag ID

        Returns:
            List[Dict[str, Any]]: List of ancestor tag data
        """
        # Use recursive CTE (Common Table Expression) to get all ancestors
        cursor = self.conn.execute(
            """
            WITH RECURSIVE ancestors(id) AS (
                SELECT parent_id FROM tag_hierarchy WHERE child_id = ?
                UNION
                SELECT th.parent_id FROM tag_hierarchy th
                JOIN ancestors a ON th.child_id = a.id
            )
            SELECT t.id, t.name, t.description
            FROM ancestors a
            JOIN tags t ON a.id = t.id
            ORDER BY t.name
            """,
            (tag_id,),
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_descendants(self, tag_id: int) -> list[dict[str, Any]]:
        """
        Get all descendant tags of a tag (recursive children).

        Args:
            tag_id: Tag ID

        Returns:
            List[Dict[str, Any]]: List of descendant tag data
        """
        # Use recursive CTE to get all descendants
        cursor = self.conn.execute(
            """
            WITH RECURSIVE descendants(id) AS (
                SELECT child_id FROM tag_hierarchy WHERE parent_id = ?
                UNION
                SELECT th.child_id FROM tag_hierarchy th
                JOIN descendants d ON th.parent_id = d.id
            )
            SELECT t.id, t.name, t.description
            FROM descendants d
            JOIN tags t ON d.id = t.id
            ORDER BY t.name
            """,
            (tag_id,),
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_siblings(self, tag_id: int) -> list[dict[str, Any]]:
        """
        Get sibling tags (tags that share a parent with the given tag).

        Args:
            tag_id: Tag ID

        Returns:
            List[Dict[str, Any]]: List of sibling tag data
        """
        cursor = self.conn.execute(
            """
            SELECT DISTINCT t.id, t.name, t.description
            FROM tag_hierarchy th1
            JOIN tag_hierarchy th2 ON th1.parent_id = th2.parent_id AND th1.child_id != th2.child_id
            JOIN tags t ON th2.child_id = t.id
            WHERE th1.child_id = ?
            ORDER BY t.name
            """,
            (tag_id,),
        )
        return [dict(row) for row in cursor.fetchall()]

    def is_ancestor(self, ancestor_id: int, descendant_id: int) -> bool:
        """
        Check if a tag is an ancestor of another tag.

        Args:
            ancestor_id: Potential ancestor tag ID
            descendant_id: Potential descendant tag ID

        Returns:
            bool: True if ancestor_id is an ancestor of descendant_id
        """
        cursor = self.conn.execute(
            """
            WITH RECURSIVE ancestors(id) AS (
                SELECT parent_id FROM tag_hierarchy WHERE child_id = ?
                UNION
                SELECT th.parent_id FROM tag_hierarchy th
                JOIN ancestors a ON th.child_id = a.id
            )
            SELECT COUNT(*) FROM ancestors WHERE id = ?
            """,
            (descendant_id, ancestor_id),
        )
        result = cursor.fetchone()
        count = int(result[0]) if result else 0
        return bool(count > 0)

    def is_related(self, tag1_id: int, tag2_id: int) -> bool:
        """
        Check if two tags are related in the hierarchy.

        Two tags are related if one is an ancestor of the other,
        or if they share a common ancestor.

        Args:
            tag1_id: First tag ID
            tag2_id: Second tag ID

        Returns:
            bool: True if the tags are related
        """
        if tag1_id == tag2_id:
            return True

        # Check if one is an ancestor of the other
        if self.is_ancestor(tag1_id, tag2_id) or self.is_ancestor(tag2_id, tag1_id):
            return True

        # Check if they share any common ancestors
        ancestors1 = {row["id"] for row in self.get_ancestors(tag1_id)}
        ancestors2 = {row["id"] for row in self.get_ancestors(tag2_id)}

        common_ancestors = ancestors1.intersection(ancestors2)
        return bool(len(common_ancestors) > 0)

    def get_path(self, tag_id: int) -> list[dict[str, Any]]:
        """
        Get the path from the root to the tag.

        If there are multiple paths, returns the shortest one.

        Args:
            tag_id: Tag ID

        Returns:
            List[Dict[str, Any]]: List of tag data in path order (root to tag)
        """
        # Get all ancestors
        ancestors = self.get_ancestors(tag_id)
        if not ancestors:
            # This tag has no ancestors, so it's a root
            cursor = self.conn.execute(
                "SELECT id, name, description FROM tags WHERE id = ?", (tag_id,)
            )
            tag = cursor.fetchone()
            if tag:
                return [dict(tag)]
            return []

        # Find roots (tags with no parents in the ancestors list)
        ancestor_ids = {a["id"] for a in ancestors}
        roots = []
        for ancestor in ancestors:
            has_parent = False
            for parent in self.get_parents(ancestor["id"]):
                if parent["id"] in ancestor_ids:
                    has_parent = True
                    break
            if not has_parent:
                roots.append(ancestor)

        # For each root, find the path to the tag
        paths = []
        for root in roots:
            path = self._find_path(root["id"], tag_id)
            if path:
                paths.append(path)

        if not paths:
            return []

        # Return the shortest path
        shortest_path = min(paths, key=len)

        # Convert tag IDs to tag data
        result = []
        for tag_id in shortest_path:
            cursor = self.conn.execute(
                "SELECT id, name, description FROM tags WHERE id = ?", (tag_id,)
            )
            tag = cursor.fetchone()
            if tag:
                result.append(dict(tag))

        return result

    def export_taxonomy(self, root_tag_id: int | None = None) -> dict[str, Any]:
        """
        Export the tag hierarchy as a nested dictionary.

        Args:
            root_tag_id: Optional root tag ID. If None, export the entire hierarchy.

        Returns:
            Dict[str, Any]: Nested dictionary representing the hierarchy
        """
        if root_tag_id is not None:
            # Export from a specific root
            return self._build_taxonomy_tree(root_tag_id)

        # Find all root tags (tags with no parents)
        cursor = self.conn.execute(
            """
            SELECT t.id, t.name, t.description
            FROM tags t
            WHERE t.id NOT IN (SELECT DISTINCT child_id FROM tag_hierarchy)
            ORDER BY t.name
            """
        )
        roots = [dict(row) for row in cursor.fetchall()]

        # Build a forest of taxonomies
        result = {}
        for root in roots:
            result[root["name"]] = self._build_taxonomy_tree(root["id"])

        return result

    def import_taxonomy(
        self, taxonomy: dict[str, Any], parent_id: int | None = None
    ) -> dict[str, int]:
        """
        Import a tag hierarchy from a nested dictionary.

        Args:
            taxonomy: Nested dictionary representing the hierarchy
            parent_id: Optional parent tag ID for the top level

        Returns:
            Dict[str, int]: Mapping of tag names to their IDs
        """
        tag_map = {}  # Map of tag names to IDs

        # First, create or get all the tags
        tags_to_process = []

        def collect_tags(tax, prefix=""):
            for name, value in tax.items():
                full_name = f"{prefix}.{name}" if prefix else name
                tags_to_process.append((full_name, None))  # (name, description)
                if isinstance(value, dict) and "children" in value:
                    collect_tags(value["children"], full_name)

        # Start with root level
        for name, value in taxonomy.items():
            desc = value.get("description") if isinstance(value, dict) else None
            tags_to_process.append((name, desc))
            if isinstance(value, dict) and "children" in value:
                collect_tags(value["children"], name)

        # Create all tags first
        for name, desc in tags_to_process:
            cursor = self.conn.execute("SELECT id FROM tags WHERE name = ?", (name,))
            row = cursor.fetchone()
            if row:
                tag_map[name] = row[0]
            else:
                cursor = self.conn.execute(
                    "INSERT INTO tags (name, description) VALUES (?, ?)", (name, desc)
                )
                self.conn.commit()
                tag_map[name] = cursor.lastrowid

        # Now create relationships
        def process_relationships(tax, parent_name=None):
            for name, value in tax.items():
                if parent_name and parent_name in tag_map and name in tag_map:
                    self.add_relationship(tag_map[parent_name], tag_map[name])

                if isinstance(value, dict) and "children" in value:
                    process_relationships(value["children"], name)

        # Process relationships
        process_relationships(taxonomy)

        # If a parent_id was provided, link all root nodes to it
        if parent_id is not None:
            for name in taxonomy.keys():
                if name in tag_map:
                    self.add_relationship(parent_id, tag_map[name])

        return tag_map

    def _would_create_cycle(self, parent_id: int, child_id: int) -> bool:
        """
        Check if adding a relationship would create a cycle.

        Args:
            parent_id: Parent tag ID
            child_id: Child tag ID

        Returns:
            bool: True if adding the relationship would create a cycle
        """
        if parent_id == child_id:
            return True

        # Check if child is already an ancestor of parent
        return self.is_ancestor(child_id, parent_id)

    def _find_path(self, start_id: int, end_id: int) -> list[int]:
        """
        Find a path from start_id to end_id in the hierarchy.

        Args:
            start_id: Starting tag ID
            end_id: Ending tag ID

        Returns:
            List[int]: List of tag IDs in path order, or empty list if no path
        """
        if start_id == end_id:
            return [start_id]

        # BFS to find shortest path
        queue = [(start_id, [start_id])]
        visited = {start_id}

        while queue:
            node, path = queue.pop(0)

            # Get children of current node
            children = self.get_children(node)
            for child in children:
                child_id = child["id"]
                if child_id == end_id:
                    return path + [child_id]

                if child_id not in visited:
                    visited.add(child_id)
                    queue.append((child_id, path + [child_id]))

        return []

    def _build_taxonomy_tree(self, tag_id: int) -> dict[str, Any]:
        """
        Build a nested dictionary representing the taxonomy tree.

        Args:
            tag_id: Root tag ID

        Returns:
            Dict[str, Any]: Nested dictionary representing the taxonomy
        """
        # Get the tag info
        cursor = self.conn.execute(
            "SELECT id, name, description FROM tags WHERE id = ?", (tag_id,)
        )
        tag = cursor.fetchone()
        if not tag:
            return {}

        result = {"id": tag["id"], "description": tag["description"]}

        # Get children
        children = self.get_children(tag_id)
        if children:
            result["children"] = {}
            for child in children:
                child_tree = self._build_taxonomy_tree(child["id"])
                if child_tree:
                    result["children"][child["name"]] = child_tree

        return result
