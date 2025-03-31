"""Relationship management module for AIchemist Codex.

This module provides the RelationshipManager class which is responsible for
creating, retrieving, and analyzing relationships between files.
"""

import json
from pathlib import Path
from typing import Any

import aiosqlite
from rich.tree import Tree


class RelationshipManager:
    """Manages file relationships in the codebase.

    The RelationshipManager provides methods for creating, retrieving,
    and analyzing relationships between files. It uses SQLite to store
    relationship data and provides methods for visualizing relationship
    networks.
    """

    def __init__(self, db_path: Path):
        """Initialize the relationship manager.

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the database and tables.

        This method creates the necessary tables if they don't exist.
        """
        if self._initialized:
            return

        async with aiosqlite.connect(self.db_path) as db:
            # Create relationships table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS relationships (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_path TEXT NOT NULL,
                    target_path TEXT NOT NULL,
                    type TEXT NOT NULL,
                    strength REAL DEFAULT 1.0,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create index for faster lookups
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_source_path
                ON relationships(source_path)
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_target_path
                ON relationships(target_path)
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_type
                ON relationships(type)
            """)

            await db.commit()

        self._initialized = True

    async def create_relationship(
        self,
        source_path: Path,
        target_path: Path,
        rel_type: str,
        strength: float = 1.0,
        metadata: dict[str, Any] | None = None,
    ) -> int:
        """Create a new relationship between files.

        Args:
            source_path: Path to the source file
            target_path: Path to the target file
            rel_type: Type of relationship (e.g., imports, references)
            strength: Strength of the relationship (0.0-1.0)
            metadata: Additional metadata for the relationship

        Returns:
            The ID of the created relationship
        """
        if not self._initialized:
            await self.initialize()

        # Serialize metadata to JSON if provided
        metadata_json = None
        if metadata:
            metadata_json = json.dumps(metadata)

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row

            # Check if relationship already exists
            cursor = await db.execute(
                """
                SELECT id FROM relationships
                WHERE source_path = ? AND target_path = ? AND type = ?
                """,
                (str(source_path), str(target_path), rel_type),
            )
            existing = await cursor.fetchone()

            if existing:
                # Update existing relationship
                await db.execute(
                    """
                    UPDATE relationships
                    SET strength = ?, metadata = ?, created_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (strength, metadata_json, existing["id"]),
                )
                relationship_id = existing["id"]
            else:
                # Create new relationship
                cursor = await db.execute(
                    """
                    INSERT INTO relationships (source_path, target_path, type, strength, metadata)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        str(source_path),
                        str(target_path),
                        rel_type,
                        strength,
                        metadata_json,
                    ),
                )
                relationship_id = cursor.lastrowid or 0  # Ensure we return an integer

            await db.commit()

        return relationship_id

    async def get_relationship(
        self, source_path: Path, target_path: Path, rel_type: str | None = None
    ) -> dict[str, Any] | None:
        """Get a specific relationship between files.

        Args:
            source_path: Path to the source file
            target_path: Path to the target file
            rel_type: Type of relationship (if None, returns any type)

        Returns:
            Dictionary with relationship details or None if not found
        """
        if not self._initialized:
            await self.initialize()

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row

            if rel_type:
                cursor = await db.execute(
                    """
                    SELECT * FROM relationships
                    WHERE source_path = ? AND target_path = ? AND type = ?
                    """,
                    (str(source_path), str(target_path), rel_type),
                )
            else:
                cursor = await db.execute(
                    """
                    SELECT * FROM relationships
                    WHERE source_path = ? AND target_path = ?
                    """,
                    (str(source_path), str(target_path)),
                )

            row = await cursor.fetchone()

            if not row:
                return None

            return self._row_to_dict(row)

    async def get_outgoing_relationships(
        self, source_path: Path, rel_type: str | None = None
    ) -> list[dict[str, Any]]:
        """Get all outgoing relationships from a file.

        Args:
            source_path: Path to the source file
            rel_type: Type of relationship to filter by (optional)

        Returns:
            List of dictionaries with relationship details
        """
        if not self._initialized:
            await self.initialize()

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row

            if rel_type:
                cursor = await db.execute(
                    """
                    SELECT * FROM relationships
                    WHERE source_path = ? AND type = ?
                    ORDER BY type, target_path
                    """,
                    (str(source_path), rel_type),
                )
            else:
                cursor = await db.execute(
                    """
                    SELECT * FROM relationships
                    WHERE source_path = ?
                    ORDER BY type, target_path
                    """,
                    (str(source_path),),
                )

            rows = await cursor.fetchall()

            return [self._row_to_dict(row) for row in rows]

    async def get_incoming_relationships(
        self, target_path: Path, rel_type: str | None = None
    ) -> list[dict[str, Any]]:
        """Get all incoming relationships to a file.

        Args:
            target_path: Path to the target file
            rel_type: Type of relationship to filter by (optional)

        Returns:
            List of dictionaries with relationship details
        """
        if not self._initialized:
            await self.initialize()

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row

            if rel_type:
                cursor = await db.execute(
                    """
                    SELECT * FROM relationships
                    WHERE target_path = ? AND type = ?
                    ORDER BY type, source_path
                    """,
                    (str(target_path), rel_type),
                )
            else:
                cursor = await db.execute(
                    """
                    SELECT * FROM relationships
                    WHERE target_path = ?
                    ORDER BY type, source_path
                    """,
                    (str(target_path),),
                )

            rows = await cursor.fetchall()

            return [self._row_to_dict(row) for row in rows]

    async def get_all_relationships(
        self, rel_type: str | None = None
    ) -> list[dict[str, Any]]:
        """Get all relationships in the system.

        Args:
            rel_type: Type of relationship to filter by (optional)

        Returns:
            List of dictionaries with relationship details
        """
        if not self._initialized:
            await self.initialize()

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row

            if rel_type:
                cursor = await db.execute(
                    """
                    SELECT * FROM relationships
                    WHERE type = ?
                    ORDER BY source_path, target_path
                    """,
                    (rel_type,),
                )
            else:
                cursor = await db.execute(
                    """
                    SELECT * FROM relationships
                    ORDER BY type, source_path, target_path
                    """
                )

            rows = await cursor.fetchall()

            return [self._row_to_dict(row) for row in rows]

    async def remove_relationship(
        self, source_path: Path, target_path: Path, rel_type: str | None = None
    ) -> int:
        """Remove relationships between files.

        Args:
            source_path: Path to the source file
            target_path: Path to the target file
            rel_type: Type of relationship to remove (if None, removes all types)

        Returns:
            Number of relationships removed
        """
        if not self._initialized:
            await self.initialize()

        async with aiosqlite.connect(self.db_path) as db:
            if rel_type:
                cursor = await db.execute(
                    """
                    DELETE FROM relationships
                    WHERE source_path = ? AND target_path = ? AND type = ?
                    """,
                    (str(source_path), str(target_path), rel_type),
                )
            else:
                cursor = await db.execute(
                    """
                    DELETE FROM relationships
                    WHERE source_path = ? AND target_path = ?
                    """,
                    (str(source_path), str(target_path)),
                )

            deleted = cursor.rowcount
            await db.commit()

        return deleted

    async def detect_relationships(
        self, file_path: Path, relationship_types: list[str] | None = None
    ) -> list[dict[str, Any]]:
        """Detect relationships between a file and other files.

        This method analyzes the file content to identify relationships
        such as imports, includes, extends, etc.

        Args:
            file_path: Path to the file to analyze
            relationship_types: Types of relationships to detect

        Returns:
            List of dictionaries with detected relationships
        """
        if not self._initialized:
            await self.initialize()

        if relationship_types is None:
            relationship_types = ["imports", "includes", "references"]

        detected_relationships = []

        # Simplified implementation for the stub
        # In a real implementation, this would analyze file content
        # to detect various types of relationships

        # For now, just return a placeholder list
        return detected_relationships

    async def visualize_relationships(
        self, files: list[Path], depth: int = 1, format: str = "tree"
    ) -> str:
        """Visualize relationships between files.

        Args:
            files: List of file paths to visualize
            depth: Depth of relationship traversal
            format: Output format (tree, dot, json)

        Returns:
            Visualization in the specified format
        """
        if not self._initialized:
            await self.initialize()

        if format == "tree":
            # Create a rich Tree visualization
            tree = Tree("File Relationships")

            for file_path in files:
                file_node = tree.add(f"[cyan]{file_path}[/]")

                # Add outgoing relationships
                outgoing = await self.get_outgoing_relationships(file_path)
                if outgoing:
                    out_node = file_node.add("[bold blue]Outgoing[/]")
                    for rel in outgoing:
                        out_node.add(
                            f"[green]{rel.get('type')}[/] → [cyan]{rel.get('target_path')}[/] "
                            f"([blue]{rel.get('strength'):.2f}[/])"
                        )

                # Add incoming relationships
                incoming = await self.get_incoming_relationships(file_path)
                if incoming:
                    in_node = file_node.add("[bold red]Incoming[/]")
                    for rel in incoming:
                        in_node.add(
                            f"[cyan]{rel.get('source_path')}[/] → [green]{rel.get('type')}[/] "
                            f"([blue]{rel.get('strength'):.2f}[/])"
                        )

            return str(tree)

        elif format == "dot":
            # Create a GraphViz DOT format
            dot_lines = ["digraph G {", "  rankdir=LR;", "  node [shape=box];"]

            # Add nodes and edges
            for file_path in files:
                file_id = self._path_to_id(file_path)
                dot_lines.append(f'  {file_id} [label="{file_path}"];')

                # Add outgoing relationships
                outgoing = await self.get_outgoing_relationships(file_path)
                for rel in outgoing:
                    target_id = self._path_to_id(rel.get("target_path"))
                    dot_lines.append(
                        f'  {file_id} -> {target_id} [label="{rel.get("type")}", '
                        f"weight={rel.get('strength', 1.0):.2f}];"
                    )

            dot_lines.append("}")
            return "\n".join(dot_lines)

        elif format == "json":
            # Create a JSON representation
            result = {"nodes": [], "edges": []}

            for file_path in files:
                # Add node
                result["nodes"].append({"id": str(file_path), "label": str(file_path)})

                # Add outgoing relationships as edges
                outgoing = await self.get_outgoing_relationships(file_path)
                for rel in outgoing:
                    result["edges"].append(
                        {
                            "source": str(file_path),
                            "target": str(rel.get("target_path")),
                            "label": rel.get("type"),
                            "weight": rel.get("strength", 1.0),
                        }
                    )

            return json.dumps(result, indent=2)

        else:
            raise ValueError(f"Unsupported format: {format}")

    def _row_to_dict(self, row: aiosqlite.Row) -> dict[str, Any]:
        """Convert a database row to a dictionary.

        Args:
            row: Database row

        Returns:
            Dictionary with relationship data
        """
        result = dict(row)

        # Parse metadata JSON if present
        if result.get("metadata"):
            try:
                result["metadata"] = json.loads(result["metadata"])
            except json.JSONDecodeError:
                result["metadata"] = {}
        else:
            result["metadata"] = {}

        # Convert paths to Path objects
        result["source_path"] = Path(result["source_path"])
        result["target_path"] = Path(result["target_path"])

        return result

    def _path_to_id(self, path: Path | str) -> str:
        """Convert a file path to a valid DOT node ID.

        Args:
            path: File path

        Returns:
            Valid DOT node ID
        """
        if path is None:
            raise ValueError("Path cannot be None")

        # Convert path to string and replace invalid characters
        path_str = str(path).replace("/", "_").replace("\\", "_").replace(".", "_")
        return f"node_{path_str}"

    async def delete_relationship(self, relationship_id: int) -> bool:
        """Delete a relationship by its ID.

        Args:
            relationship_id: ID of the relationship to delete

        Returns:
            True if the relationship was deleted, False otherwise
        """
        if not self._initialized:
            await self.initialize()

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                DELETE FROM relationships WHERE id = ?
                """,
                (relationship_id,),
            )
            await db.commit()

            # Verify the relationship was deleted
            cursor = await db.execute(
                """
                SELECT id FROM relationships WHERE id = ?
                """,
                (relationship_id,),
            )
            row = await cursor.fetchone()

            return row is None

    async def delete_relationship_by_paths(
        self, source_path: Path, target_path: Path, rel_type: str
    ) -> bool:
        """Delete a relationship between two files of a specific type.

        Args:
            source_path: Path to the source file
            target_path: Path to the target file
            rel_type: Type of relationship to delete

        Returns:
            True if the relationship was deleted, False otherwise
        """
        if not self._initialized:
            await self.initialize()

        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                DELETE FROM relationships
                WHERE source_path = ? AND target_path = ? AND type = ?
                """,
                (str(source_path), str(target_path), rel_type),
            )
            await db.commit()

            return cursor.rowcount > 0

    async def delete_relationships_between(
        self, source_path: Path, target_path: Path
    ) -> int:
        """Delete all relationships between two files.

        Args:
            source_path: Path to the source file
            target_path: Path to the target file

        Returns:
            Number of relationships deleted
        """
        if not self._initialized:
            await self.initialize()

        async with aiosqlite.connect(self.db_path) as db:
            # Delete relationships in both directions
            cursor1 = await db.execute(
                """
                DELETE FROM relationships
                WHERE source_path = ? AND target_path = ?
                """,
                (str(source_path), str(target_path)),
            )

            cursor2 = await db.execute(
                """
                DELETE FROM relationships
                WHERE source_path = ? AND target_path = ?
                """,
                (str(target_path), str(source_path)),
            )

            await db.commit()

            return cursor1.rowcount + cursor2.rowcount

    async def get_relationship_network(
        self,
        center_path: Path,
        include_incoming: bool = True,
        include_outgoing: bool = True,
        max_depth: int = 1,
    ) -> dict[str, list[dict[str, Any]]]:
        """Get a network of relationships centered around a file.

        This method traverses the relationship graph starting from a center file,
        following relationships outward up to the specified depth.

        Args:
            center_path: Path to the center file
            include_incoming: Include incoming relationships
            include_outgoing: Include outgoing relationships
            max_depth: Maximum depth for traversal (1 = direct relationships only)

        Returns:
            Dictionary with nodes and edges lists
        """
        if not self._initialized:
            await self.initialize()

        # Track visited nodes to avoid cycles
        visited = set()
        # Map file paths to node IDs
        path_to_id = {}
        # Store nodes and edges
        nodes = []
        edges = []

        async def traverse(path: Path, depth: int = 0):
            # Skip if we've visited this node or reached max depth
            if str(path) in visited or depth > max_depth:
                return

            # Mark as visited
            visited.add(str(path))

            # Add node if new
            if str(path) not in path_to_id:
                node_id = len(nodes) + 1
                path_to_id[str(path)] = node_id
                nodes.append({"id": node_id, "path": str(path)})

            # Stop traversal at max depth
            if depth == max_depth:
                return

            # Get outgoing relationships
            if include_outgoing:
                outgoing = await self.get_outgoing_relationships(path)
                for rel in outgoing:
                    target = Path(rel["target_path"])

                    # Add target node if new
                    if str(target) not in path_to_id:
                        target_id = len(nodes) + 1
                        path_to_id[str(target)] = target_id
                        nodes.append({"id": target_id, "path": str(target)})

                    # Add edge
                    edges.append(
                        {
                            "source_id": path_to_id[str(path)],
                            "target_id": path_to_id[str(target)],
                            "type": rel["type"],
                            "strength": rel["strength"],
                        }
                    )

                    # Recursively traverse target
                    await traverse(target, depth + 1)

            # Get incoming relationships
            if include_incoming:
                incoming = await self.get_incoming_relationships(path)
                for rel in incoming:
                    source = Path(rel["source_path"])

                    # Add source node if new
                    if str(source) not in path_to_id:
                        source_id = len(nodes) + 1
                        path_to_id[str(source)] = source_id
                        nodes.append({"id": source_id, "path": str(source)})

                    # Add edge
                    edges.append(
                        {
                            "source_id": path_to_id[str(source)],
                            "target_id": path_to_id[str(path)],
                            "type": rel["type"],
                            "strength": rel["strength"],
                        }
                    )

                    # Recursively traverse source
                    await traverse(source, depth + 1)

        # Start traversal from center path
        await traverse(center_path)

        return {
            "nodes": nodes,
            "edges": edges,
        }
