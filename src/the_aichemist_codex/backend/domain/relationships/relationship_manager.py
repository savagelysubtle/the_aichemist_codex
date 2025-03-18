"""
Relationship management functionality.

This module provides the RelationshipManagerImpl class for managing
file relationships, including creating, updating, and querying relationships.
"""

import logging
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from ....core.exceptions import FileError, RelationshipError, UnsafePathError
from ....core.interfaces import RelationshipManager as RelationshipManagerInterface
from ....core.models import RelationshipType
from ....registry import Registry
from .detector import RelationshipDetector
from .relationship import Relationship
from .schema import RelationshipSchema

logger = logging.getLogger(__name__)


class RelationshipManagerImpl(RelationshipManagerInterface):
    """
    Implementation of the RelationshipManager interface.

    This class provides methods for managing relationships between files,
    including creating, retrieving, updating, and deleting relationships.
    It also provides methods for querying relationships and analyzing file
    connections.
    """

    def __init__(self):
        """Initialize the RelationshipManagerImpl."""
        self._registry = Registry.get_instance()
        self._validator = self._registry.file_validator
        self._paths = self._registry.project_paths

        # Get the path to the relationship database file
        self._db_path = self._paths.get_data_dir() / "relationships.db"
        self._schema = RelationshipSchema(self._db_path)

        # Initialize the relationship detector
        self._detector = RelationshipDetector()

    async def initialize(self) -> None:
        """
        Initialize the relationship manager and create database tables if needed.

        Raises:
            Exception: If initialization fails
        """
        await self._schema.initialize()
        logger.info("Initialized RelationshipManager")

    async def close(self) -> None:
        """Close any resources used by the relationship manager."""
        logger.debug("Closed RelationshipManager")

    async def add_relationship(
        self,
        source_path: Path,
        target_path: Path,
        rel_type: str,
        strength: float = 1.0,
        metadata: dict[str, Any] = None,
    ) -> str:
        """
        Add a relationship between two files.

        Args:
            source_path: Path to the source file
            target_path: Path to the target file
            rel_type: Type of relationship (see RelationshipType enum)
            strength: Strength of the relationship (0.0 to 1.0)
            metadata: Additional metadata for the relationship

        Returns:
            The ID of the newly created relationship

        Raises:
            RelationshipError: If relationship creation fails
            FileError: If either file does not exist
        """
        try:
            # Ensure files exist and paths are safe
            source_path = Path(str(source_path))
            target_path = Path(str(target_path))
            source_path_str = str(source_path)
            target_path_str = str(target_path)

            self._validator.ensure_path_safe(source_path_str)
            self._validator.ensure_path_safe(target_path_str)

            if not os.path.exists(source_path):
                raise FileError(
                    f"Source file does not exist: {source_path}",
                    file_path=source_path_str,
                )

            if not os.path.exists(target_path):
                raise FileError(
                    f"Target file does not exist: {target_path}",
                    file_path=target_path_str,
                )

            # Validate relationship type
            try:
                rel_type_enum = RelationshipType[rel_type]
            except KeyError:
                valid_types = ", ".join(t.name for t in RelationshipType)
                raise RelationshipError(
                    f"Invalid relationship type: {rel_type}. Valid types are: {valid_types}",
                    rel_type=rel_type,
                )

            # Create a relationship object
            relationship = Relationship(
                source_path=source_path,
                target_path=target_path,
                rel_type=rel_type_enum,
                strength=strength,
                metadata=metadata,
            )

            # Store the relationship in the database
            conn = await self._schema.get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO relationships
                    (id, source_path, target_path, rel_type, strength, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        relationship.id,
                        source_path_str,
                        target_path_str,
                        rel_type,
                        relationship.strength,
                        self._schema.serialize_metadata(relationship.metadata),
                    ),
                )
                conn.commit()
                return relationship.id
            except sqlite3.Error as e:
                logger.error(f"Database error adding relationship: {e}")
                raise RelationshipError(
                    f"Failed to add relationship: {e}",
                    source_path=source_path_str,
                    target_path=target_path_str,
                    rel_type=rel_type,
                )
            finally:
                conn.close()
        except Exception as e:
            if isinstance(e, (RelationshipError, FileError, UnsafePathError)):
                raise
            logger.error(f"Error adding relationship: {e}")
            raise RelationshipError(
                f"Failed to add relationship: {e}",
                source_path=str(source_path),
                target_path=str(target_path),
                rel_type=rel_type,
            )

    async def get_relationship(self, relationship_id: str) -> dict[str, Any] | None:
        """
        Get relationship information by ID.

        Args:
            relationship_id: ID of the relationship to retrieve

        Returns:
            Relationship information as a dictionary, or None if not found
        """
        try:
            conn = await self._schema.get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT id, source_path, target_path, rel_type, strength,
                           created_at, modified_at, metadata
                    FROM relationships
                    WHERE id = ?
                    """,
                    (relationship_id,),
                )
                row = cursor.fetchone()
                if row:
                    return self._row_to_dict(row)
                return None
            finally:
                conn.close()
        except Exception as e:
            logger.error(f"Error getting relationship: {e}")
            raise RelationshipError(
                f"Failed to get relationship: {e}", relationship_id=relationship_id
            )

    async def update_relationship(
        self,
        relationship_id: str,
        rel_type: str = None,
        strength: float = None,
        metadata: dict[str, Any] = None,
    ) -> bool:
        """
        Update an existing relationship.

        Args:
            relationship_id: ID of the relationship to update
            rel_type: New type for the relationship (optional)
            strength: New strength for the relationship (optional)
            metadata: New metadata for the relationship (optional)

        Returns:
            True if the relationship was updated, False otherwise

        Raises:
            RelationshipError: If the relationship does not exist or the update fails
        """
        if rel_type is None and strength is None and metadata is None:
            return False

        try:
            # Get the relationship to make sure it exists
            relationship_data = await self.get_relationship(relationship_id)
            if not relationship_data:
                raise RelationshipError(
                    f"Relationship with ID {relationship_id} does not exist",
                    relationship_id=relationship_id,
                )

            # Prepare update values
            updates = []
            params = []

            if rel_type is not None:
                # Validate relationship type
                try:
                    RelationshipType[rel_type]
                except KeyError:
                    valid_types = ", ".join(t.name for t in RelationshipType)
                    raise RelationshipError(
                        f"Invalid relationship type: {rel_type}. Valid types are: {valid_types}",
                        rel_type=rel_type,
                    )
                updates.append("rel_type = ?")
                params.append(rel_type)

            if strength is not None:
                # Clamp strength to [0, 1]
                strength = max(0.0, min(1.0, strength))
                updates.append("strength = ?")
                params.append(strength)

            if metadata is not None:
                # Merge with existing metadata
                existing_metadata = self._schema.deserialize_metadata(
                    relationship_data.get("metadata", "{}")
                )
                existing_metadata.update(metadata)
                updates.append("metadata = ?")
                params.append(self._schema.serialize_metadata(existing_metadata))

            updates.append("modified_at = CURRENT_TIMESTAMP")

            # Add relationship_id to params
            params.append(relationship_id)

            # Execute update
            conn = await self._schema.get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(
                    f"UPDATE relationships SET {', '.join(updates)} WHERE id = ?",
                    tuple(params),
                )
                conn.commit()
                return cursor.rowcount > 0
            finally:
                conn.close()
        except Exception as e:
            if isinstance(e, RelationshipError):
                raise
            logger.error(f"Error updating relationship: {e}")
            raise RelationshipError(
                f"Failed to update relationship: {e}", relationship_id=relationship_id
            )

    async def delete_relationship(self, relationship_id: str) -> bool:
        """
        Delete a relationship.

        Args:
            relationship_id: ID of the relationship to delete

        Returns:
            True if the relationship was deleted, False otherwise

        Raises:
            RelationshipError: If the relationship does not exist or the deletion fails
        """
        try:
            # Get the relationship to make sure it exists
            relationship = await self.get_relationship(relationship_id)
            if not relationship:
                raise RelationshipError(
                    f"Relationship with ID {relationship_id} does not exist",
                    relationship_id=relationship_id,
                )

            conn = await self._schema.get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM relationships WHERE id = ?", (relationship_id,)
                )
                conn.commit()
                return cursor.rowcount > 0
            finally:
                conn.close()
        except Exception as e:
            if isinstance(e, RelationshipError):
                raise
            logger.error(f"Error deleting relationship: {e}")
            raise RelationshipError(
                f"Failed to delete relationship: {e}", relationship_id=relationship_id
            )

    async def get_relationships_for_file(
        self, file_path: Path, as_source: bool = True, as_target: bool = True
    ) -> list[dict[str, Any]]:
        """
        Get all relationships for a file.

        Args:
            file_path: Path to the file
            as_source: Include relationships where the file is the source
            as_target: Include relationships where the file is the target

        Returns:
            List of dictionaries containing relationship information
        """
        try:
            # Ensure path is safe
            file_path = Path(str(file_path))
            file_path_str = str(file_path)
            self._validator.ensure_path_safe(file_path_str)

            if not as_source and not as_target:
                return []

            conn = await self._schema.get_connection()
            try:
                cursor = conn.cursor()
                results = []

                if as_source and as_target:
                    cursor.execute(
                        """
                        SELECT id, source_path, target_path, rel_type, strength,
                               created_at, modified_at, metadata
                        FROM relationships
                        WHERE source_path = ? OR target_path = ?
                        ORDER BY rel_type, strength DESC
                        """,
                        (file_path_str, file_path_str),
                    )
                elif as_source:
                    cursor.execute(
                        """
                        SELECT id, source_path, target_path, rel_type, strength,
                               created_at, modified_at, metadata
                        FROM relationships
                        WHERE source_path = ?
                        ORDER BY rel_type, strength DESC
                        """,
                        (file_path_str,),
                    )
                else:  # as_target
                    cursor.execute(
                        """
                        SELECT id, source_path, target_path, rel_type, strength,
                               created_at, modified_at, metadata
                        FROM relationships
                        WHERE target_path = ?
                        ORDER BY rel_type, strength DESC
                        """,
                        (file_path_str,),
                    )

                for row in cursor.fetchall():
                    results.append(self._row_to_dict(row))

                return results
            finally:
                conn.close()
        except Exception as e:
            if isinstance(e, UnsafePathError):
                raise
            logger.error(f"Error getting relationships for file: {e}")
            raise RelationshipError(f"Failed to get relationships for file: {e}")

    async def find_related_files(
        self, file_path: Path, rel_types: list[str] = None, min_strength: float = 0.0
    ) -> list[dict[str, Any]]:
        """
        Find files related to the given file.

        Args:
            file_path: Path to the file
            rel_types: Types of relationships to include (optional)
            min_strength: Minimum relationship strength (0.0 to 1.0)

        Returns:
            List of dictionaries containing related file information and relationship details
        """
        try:
            # Ensure path is safe
            file_path = Path(str(file_path))
            file_path_str = str(file_path)
            self._validator.ensure_path_safe(file_path_str)

            # Build the query
            query_parts = []
            params = []

            # Base query for related files
            query_base = """
                SELECT id, source_path, target_path, rel_type, strength,
                       created_at, modified_at, metadata
                FROM relationships
                WHERE
            """

            # Condition for finding relationships where the file is either source or target
            query_parts.append("(source_path = ? OR target_path = ?)")
            params.extend([file_path_str, file_path_str])

            # Filter by relationship types if specified
            if rel_types and len(rel_types) > 0:
                # Validate relationship types
                for rel_type in rel_types:
                    try:
                        RelationshipType[rel_type]
                    except KeyError:
                        valid_types = ", ".join(t.name for t in RelationshipType)
                        raise RelationshipError(
                            f"Invalid relationship type: {rel_type}. Valid types are: {valid_types}",
                            rel_type=rel_type,
                        )

                placeholders = ", ".join("?" for _ in rel_types)
                query_parts.append(f"rel_type IN ({placeholders})")
                params.extend(rel_types)

            # Filter by minimum strength
            if min_strength > 0:
                query_parts.append("strength >= ?")
                params.append(min_strength)

            # Combine the query parts
            query = f"{query_base} {' AND '.join(query_parts)} ORDER BY strength DESC"

            # Execute the query
            conn = await self._schema.get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(query, tuple(params))
                results = []

                for row in cursor.fetchall():
                    rel_dict = self._row_to_dict(row)

                    # Determine the related file path
                    source = rel_dict["source_path"]
                    target = rel_dict["target_path"]
                    related_path = target if source == file_path_str else source

                    # Add the related file info
                    rel_dict["related_file"] = related_path
                    rel_dict["direction"] = (
                        "outgoing" if source == file_path_str else "incoming"
                    )

                    results.append(rel_dict)

                return results
            finally:
                conn.close()
        except Exception as e:
            if isinstance(e, (UnsafePathError, RelationshipError)):
                raise
            logger.error(f"Error finding related files: {e}")
            raise RelationshipError(f"Failed to find related files: {e}")

    async def detect_relationships(
        self, file_path: Path, strategies: list[str] = None
    ) -> list[dict[str, Any]]:
        """
        Detect relationships for a file using various detection strategies.

        Args:
            file_path: Path to the file
            strategies: List of detection strategy names (optional)

        Returns:
            List of detected relationships

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

            # Detect relationships
            relationships = await self._detector.detect_relationships(
                file_path, strategies
            )

            # Convert to dictionaries
            results = []
            for rel in relationships:
                # Add the relationship to the database
                rel_id = await self.add_relationship(
                    rel.source_path,
                    rel.target_path,
                    rel.rel_type.name,
                    rel.strength,
                    rel.metadata,
                )

                # Get the relationship from the database
                rel_dict = await self.get_relationship(rel_id)
                if rel_dict:
                    results.append(rel_dict)

            return results
        except Exception as e:
            if isinstance(e, (FileError, UnsafePathError)):
                raise
            logger.error(f"Error detecting relationships: {e}")
            raise RelationshipError(f"Failed to detect relationships: {e}")

    async def get_relationship_graph(
        self, root_file: Path = None, max_depth: int = 2, min_strength: float = 0.0
    ) -> dict[str, Any]:
        """
        Get a graph representation of file relationships.

        Args:
            root_file: Starting file for the graph (optional)
            max_depth: Maximum depth of relationships to traverse
            min_strength: Minimum relationship strength (0.0 to 1.0)

        Returns:
            Dictionary representing the relationship graph
        """
        try:
            # Validate root file if provided
            if root_file:
                root_file = Path(str(root_file))
                root_file_str = str(root_file)
                self._validator.ensure_path_safe(root_file_str)

                if not os.path.exists(root_file):
                    raise FileError(
                        f"File does not exist: {root_file}", file_path=root_file_str
                    )
            else:
                # Use project root if no file is specified
                root_file = self._paths.get_project_root()
                root_file_str = str(root_file)

            # Initialize the graph
            graph = {
                "nodes": [],
                "edges": [],
                "metadata": {
                    "root_file": root_file_str,
                    "max_depth": max_depth,
                    "min_strength": min_strength,
                    "generated_at": datetime.now().isoformat(),
                },
            }

            # Keep track of processed nodes to avoid cycles
            processed_nodes: set[str] = set()
            node_ids: dict[str, int] = {}
            next_node_id = 0

            async def add_node(file_path: str) -> int:
                if file_path not in node_ids:
                    node_ids[file_path] = next_node_id
                    graph["nodes"].append(
                        {
                            "id": next_node_id,
                            "file_path": file_path,
                            "label": Path(file_path).name,
                        }
                    )
                    nonlocal next_node_id
                    next_node_id += 1
                return node_ids[file_path]

            async def process_file(file_path: str, current_depth: int):
                if current_depth > max_depth or file_path in processed_nodes:
                    return

                processed_nodes.add(file_path)
                source_node_id = await add_node(file_path)

                # Get related files
                related_files = await self.find_related_files(
                    Path(file_path), min_strength=min_strength
                )

                for rel in related_files:
                    related_path = rel["related_file"]
                    target_node_id = await add_node(related_path)

                    # Add the edge
                    graph["edges"].append(
                        {
                            "source": source_node_id
                            if rel["direction"] == "outgoing"
                            else target_node_id,
                            "target": target_node_id
                            if rel["direction"] == "outgoing"
                            else source_node_id,
                            "type": rel["rel_type"],
                            "strength": rel["strength"],
                            "metadata": rel["metadata"],
                        }
                    )

                    # Process the related file recursively
                    await process_file(related_path, current_depth + 1)

            # Start processing from the root file
            await process_file(root_file_str, 0)

            return graph
        except Exception as e:
            if isinstance(e, (FileError, UnsafePathError)):
                raise
            logger.error(f"Error generating relationship graph: {e}")
            raise RelationshipError(f"Failed to generate relationship graph: {e}")

    def _row_to_dict(self, row: sqlite3.Row) -> dict[str, Any]:
        """
        Convert a database row to a dictionary.

        Args:
            row: The database row

        Returns:
            Dictionary representation of the row
        """
        result = dict(row)

        # Convert metadata from JSON string to dictionary
        result["metadata"] = self._schema.deserialize_metadata(result.get("metadata"))

        return result


# Export symbols
__all__ = ["RelationshipManagerImpl"]
